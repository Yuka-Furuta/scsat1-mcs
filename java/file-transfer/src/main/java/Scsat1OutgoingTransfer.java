package org.yamcs.cfdp;

import static org.yamcs.cfdp.CfdpService.ETYPE_TRANSFER_FINISHED;
import static org.yamcs.cfdp.CfdpService.ETYPE_TRANSFER_RESUMED;
import static org.yamcs.cfdp.CfdpService.ETYPE_TRANSFER_SUSPENDED;

import java.util.Arrays;
import java.util.Map;
import java.util.concurrent.ScheduledFuture;
import java.util.concurrent.ScheduledThreadPoolExecutor;
import java.util.concurrent.TimeUnit;

import org.yamcs.YConfiguration;
import org.yamcs.cfdp.pdu.CfdpPacket;
import org.yamcs.cfdp.pdu.ConditionCode;
import org.yamcs.events.EventProducer;
import org.yamcs.filetransfer.TransferMonitor;
import org.yamcs.protobuf.TransferDirection;
import org.yamcs.protobuf.TransferState;
import org.yamcs.yarch.Bucket;
import org.yamcs.yarch.Stream;

// テスト
import java.net.DatagramSocket;
import java.net.DatagramPacket;
import java.net.InetAddress;
import java.net.SocketException;
import java.net.UnknownHostException;
import java.io.IOException;
import org.yamcs.tctm.csp.CspPacket;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;

public class Scsat1OutgoingTransfer extends OngoingCfdpTransfer {
    // テスト
    protected DatagramSocket socket;
    protected int port;
    protected String host;
    protected InetAddress address;
    private byte[] sendData;
    private CspPacket cspFilePacket;
    private int sessionId = 0;
    private byte[] fileSendPacket;
    private int fileSendPacketLength;
    private final int sendDataMaxSize = 200;
    private int offset;
    private int remainSize;

    private static final String STORAGE_NAME = "/storage/";
    private static final int CMD_OPEN = 2;
    private static final int CMD_DATA = 3;
    private static final int CMD_CLOSE = 4;

    private enum OutTxState {
        /**
         * Initial state. Going to SENDING_DATA in the first sendPdu step.
         */
        START,
        /**
         * Sending data and EOF. Going to FINISHED as soon as the Finished PDU is received.
         */
        SENDING_DATA,
        /**
         * Sending CANCEL EOF Going to COMPLETED as soon as the CANCEL EOF ACK is received
         */
        CANCELING,
        /**
         * End state. Still sending FINISHED ACK in return of Finished PDUs.
         */
        COMPLETED,
    }


    private Bucket bucket;
    private final int sleepBetweenPdus;

    private OutTxState outTxState;
    private long transferred;

    private boolean suspended = false;

    private PutRequest request;
    private ScheduledFuture<?> pduSendingSchedule;

    boolean eofSent = false;
    ConditionCode reasonForCancellation;

    /**
     * Create a new CFDP outgoing (uplink) transfer.
     * <p>
     * The transfer has to be started with the {@link #start()} method.
     *
     * @param yamcsInstance
     *            - yamcsInstance where this transfer is running. It is used for log configuration and to get the time
     *            service.
     * @param initiatorEntityId
     * @param id
     *            - unique identifier. The least significant number of bits (according to the CFDP sequence length) of
     *            this id will be used to make the CFDP transaction id.
     * @param creationTime
     *            - time when the transaction has been created
     * @param executor
     *            - the CFDP state machine is serialized in this executor. It is also used to schedule timeouts.
     * @param request
     *            - the request containing the file to be sent.
     * @param cfdpOut
     *            - the stream where the outgoing PDUs are placed.
     * @param config
     *            - the configuration of various settings (see yamcs manual)
     * @param bucket
     *            - bucket from/to which the file should be
     * @param customPduSize
     *            - if not null, size to overwrite the config maxPduSize
     * @param customPduDelay
     *            - if not null, delay to overwrite the config sleepBetweenPdus
     * @param eventProducer
     *            - used to send events when important things happen
     * @param monitor
     *            - will be notified when transaction status changes
     * @param faultHandlerActions
     *            - can be used to change behaviour in case of timeouts or failures. Can be null, in which case the
     *            default behaviour to cancel the transaction will be used.
     */
    public Scsat1OutgoingTransfer(String yamcsInstance, long initiatorEntityId, long id, long creationTime,
            ScheduledThreadPoolExecutor executor,
            PutRequest request, Stream cfdpOut, YConfiguration config, Bucket bucket,
            Integer customPduSize, Integer customPduDelay,
            EventProducer eventProducer,
            TransferMonitor monitor, Map<ConditionCode, FaultHandlingAction> faultHandlerActions) {
        super(yamcsInstance, id, creationTime,
                executor, config, makeTransactionId(initiatorEntityId, config, id),
                request.getDestinationCfdpEntityId(), cfdpOut,
                eventProducer, monitor, faultHandlerActions);
        this.request = request;
        this.bucket = bucket;

        host = config.getString("host");
        port = config.getInt("port");
        outTxState = OutTxState.START;
        this.sleepBetweenPdus = customPduDelay != null && customPduDelay > 0 ? customPduDelay
                : config.getInt("sleepBetweenPdus", 500);
    }

    private static CfdpTransactionId makeTransactionId(long sourceId, YConfiguration config, long id) {
        // makeTransactionIdは必要なので固定値にした
        int seqNrSize = 4;
        long seqNum = id & ((1l << seqNrSize * 8) - 1);

        return new CfdpTransactionId(sourceId, seqNum);
    }

    /**
     * Start the transfer
     */
    public void start() {
        // socketの設定をする
        try {
            setUdpSender();
        } catch (SocketException | UnknownHostException e) {
            e.printStackTrace();
            return;
        }
        pduSendingSchedule = executor.scheduleAtFixedRate(this::sendPDU, 0, sleepBetweenPdus, TimeUnit.MILLISECONDS);
    }

    private void sendPDU() {
        if (suspended) {
            return;
        }
        try {
            switch (outTxState) {
                case START:
                    System.out.println("Start!!!!");
                    uploadOpenCmd();
                    offset = 0;
                    remainSize = request.getFileLength();
                    this.outTxState = OutTxState.SENDING_DATA;
                    monitor.stateChanged(this);
                    break;
                case SENDING_DATA:
                    System.out.println("Sending!!!!");
                    uploadDataCmd();
                    monitor.stateChanged(this);
                    break;
                case COMPLETED:
                    System.out.println("Fin!!!!");
                    pduSendingSchedule.cancel(true);
                    cancelInactivityTimer();
                    break;
                default:
                    throw new IllegalStateException("unknown/illegal state");
            }
        }  catch (Exception e) {
                log.error("Error when sending command: ", e);
                throw new RuntimeException(e);
        }
    }

    // ByteArray変換系
    public byte[] concat(byte[] a, byte[] b) {
        byte[] result = new byte[a.length + b.length];
        System.arraycopy(a, 0, result, 0, a.length);
        System.arraycopy(b, 0, result, a.length, b.length);
        return result;
    }

    public byte[] fileSendPacketHeader(int commandId, int sessionId) {
        // 1バイト: commandId, 2バイト: sessionId, sessionId は little-endian
        ByteBuffer buffer = ByteBuffer.allocate(1 + 2);
        buffer.order(ByteOrder.LITTLE_ENDIAN);
        buffer.put((byte) commandId);
        buffer.putShort((short) sessionId);
        return buffer.array();
    }

    public byte[] fileName2ByteArray(String fileName) {
        ByteBuffer buffer = ByteBuffer.allocate(64);
        byte[] fileNameBytes = fileName.getBytes(StandardCharsets.UTF_8);
        if (fileNameBytes.length > 64) {
            throw new IllegalArgumentException("fileName toofileSendPacketLength long (max 64 bytes in UTF-8)");
        }
        buffer.put(fileNameBytes);
        buffer.put(new byte[64 - fileNameBytes.length]); // ゼロ埋め
        return buffer.array();
    }

    public byte[] fileData2ByteArray(int offset, int sendFileSize, byte[] fileData) {
        // offset (4バイト), sendFileSize (4バイト), fileData（200byte）
        ByteBuffer buffer = ByteBuffer.allocate(4 + 4 + 200); // 必要なバイト数を確保
        int fileDataLength = Math.min(fileData.length, 200); // fileDataの長さが200を超えないようにする
        buffer.order(ByteOrder.LITTLE_ENDIAN); // リトルエンディアン
        buffer.putInt(offset);
        buffer.putInt(sendFileSize);
        buffer.put(fileData, 0, fileDataLength);
        // 足りない分はゼロで埋める
        if (fileDataLength < 200) {
            buffer.put(new byte[200 - fileDataLength]); // ゼロ埋め
        }
        return buffer.array();
    }

    // socket,addressの設定
    public void setUdpSender() throws SocketException, UnknownHostException {
        socket = new DatagramSocket();
        address = InetAddress.getByName(host);
    }

    // テスト用　消す
    public static void printHex(byte[] data) {
        for (byte b : data) {
            System.out.printf("%02X ", b); // 2桁の16進数、先頭にゼロ埋め
        }
        System.out.println();
    }


    public void sendFileCommand(byte[] data) throws IOException {
        ByteBuffer buf = ByteBuffer.allocate(4 + data.length);
        cspFilePacket = new CspPacket(buf);
        int filePriority = 2;
        byte src = (byte) cfdpTransactionId.getInitiatorEntity();
        byte dst = (byte) request.getDestinationCfdpEntityId();
        int fileDport = 13;
        cspFilePacket.setHeader((byte)filePriority, src, dst, (byte)fileDport, (byte)32);
        // 4. ヘッダの後ろにデータを書き込む
        buf.position(4);
        buf.put(data);
        fileSendPacket = cspFilePacket.getBytes();
        fileSendPacketLength = cspFilePacket.getLength();
        printHex(fileSendPacket);
        DatagramPacket packet = new DatagramPacket(fileSendPacket, fileSendPacketLength, address, port);
        socket.send(packet);
    }

    // Command送信シリーズ
    public void uploadOpenCmd()  throws IOException {
        String fileName = STORAGE_NAME + request.getDestinationFileName();
        byte[] openFileHeader = fileSendPacketHeader(CMD_OPEN, sessionId);
        byte[] openFileName = fileName2ByteArray(fileName);
        sendData = concat(openFileHeader, openFileName);
        sendFileCommand(sendData);
    }

    public void uploadDataCmd()  throws IOException {
        System.out.println(remainSize);
        int sendFileSize = 0; // uint32, little
        byte[] fileDataChunk; // binary, 1600bits
        byte[] uploadFileData;
        byte[] uploadFileHeader = fileSendPacketHeader(CMD_DATA, sessionId);
        if(remainSize == 0){
            if (offset % sendDataMaxSize == 0){
                // 全部キレイに送れてしまったとき？終了通知
                offset = 0;
                sendFileSize = 0;
                fileDataChunk = new byte[0];
                uploadFileData = fileData2ByteArray(offset, sendFileSize, fileDataChunk);
                sendData = concat(uploadFileHeader, uploadFileData);
                sendFileCommand(sendData);
            }
            uploadCloseCmd();
        } else {
            if (remainSize < sendDataMaxSize){
                sendFileSize = remainSize;
            } else {
                sendFileSize = sendDataMaxSize;
            }
            // 塊データchunk をsize分読み込む
            fileDataChunk = Arrays.copyOfRange(request.getFileData(), offset, offset + sendFileSize);
            // 送る
            uploadFileData = fileData2ByteArray(offset, sendFileSize, fileDataChunk);
            sendData = concat(uploadFileHeader, uploadFileData);
            sendFileCommand(sendData);
            offset = offset + sendFileSize;
            remainSize = remainSize - sendFileSize;
        }
    }

    public void uploadCloseCmd() throws IOException {
        System.out.println("Close");
        sendData = fileSendPacketHeader(CMD_CLOSE, sessionId);
        sendFileCommand(sendData);
        close();
        complete(ConditionCode.NO_ERROR);
        eofSent = true;
    }

    public void close() {
        socket.close();
    }


    @Override
    public void processPacket(CfdpPacket packet) {
        executor.submit(() -> doProcessPacket(packet));
    }

    private void doProcessPacket(CfdpPacket packet) {
        if (state == TransferState.COMPLETED || state == TransferState.FAILED) {
            return;
        }
    }


    /**
     * The inactivity timer is active after the EOF ACK has been received
     */
    @Override
    protected void onInactivityTimerExpiration() {
        log.warn("TXID{} Inactivity timeout while in {} state; transaction failed", cfdpTransactionId,
                outTxState);
        handleFault(ConditionCode.INACTIVITY_DETECTED);
    }

    @Override
    protected void suspend() {
        if (outTxState == OutTxState.COMPLETED) {
            log.info("TXID{} transfer finished, suspend ignored", cfdpTransactionId);
            return;
        }
        sendInfoEvent(ETYPE_TRANSFER_SUSPENDED, "transfer suspended");
        log.info("TXID{} suspending transfer", cfdpTransactionId);
        pduSendingSchedule.cancel(true);
        cancelInactivityTimer();
        suspended = true;
        changeState(TransferState.PAUSED);
    }

    @Override
    protected void resume() {
        if (!suspended) {
            log.info("TXID{} resume called while not suspended, ignoring", cfdpTransactionId);
            return;
        }
        if (outTxState == OutTxState.COMPLETED) {
            // it is possible the transfer has finished while being suspended
            log.info("TXID{} transfer finished, suspend ignored", cfdpTransactionId);
            return;
        }
        log.info("TXID{} resuming transfer", cfdpTransactionId);
        sendInfoEvent(ETYPE_TRANSFER_RESUMED, "transfer resumed");
        pduSendingSchedule = executor.scheduleAtFixedRate(this::sendPDU, 0, sleepBetweenPdus, TimeUnit.MILLISECONDS);
        rescheduleInactivityTimer();
        changeState(TransferState.RUNNING);
        suspended = false;
    }

    public OutTxState getCfdpState() {
        return this.outTxState;
    }

    private void complete(ConditionCode conditionCode) {
        if (outTxState == OutTxState.COMPLETED) {
            return;
        }
        outTxState = OutTxState.COMPLETED;
        // 転送開始からの経過時間を秒単位で算出。
        long duration = (System.currentTimeMillis() - wallclockStartTime) / 1000;
        // 状態遷移 → COMPLETED
        // 成功メッセージを INFO イベントで送信
        // とりあえずこれで成功メッセージ
        String eventMessageSuffix = request.getSourceFileName() + " -> " + request.getDestinationFileName();
        if (conditionCode == ConditionCode.NO_ERROR) {
            changeState(TransferState.COMPLETED);
            sendInfoEvent(ETYPE_TRANSFER_FINISHED,
                    "transfer finished successfully in " + duration + " seconds: "
                            + eventMessageSuffix);
        } else {
            // エラーとして処理 (failTransfer)
            // 警告イベントとして、詳細含めて送信
            failTransfer(conditionCode.toString());
            sendWarnEvent(ETYPE_TRANSFER_FINISHED,
                    "transfer finished with error in " + duration + " seconds: "
                            + eventMessageSuffix );
        }
    }

    @Override
    protected void cancel(ConditionCode conditionCode) {
        log.debug("TXID{} Cancelling with code {}", cfdpTransactionId, conditionCode);
        try {
            switch (outTxState) {
                case START:
                case SENDING_DATA:
                    reasonForCancellation = conditionCode;
                    suspended = false; // wake up if sleeping
                    outTxState = OutTxState.CANCELING;
                    changeState(TransferState.CANCELLING);
                    uploadCloseCmd();
                    break;
                case CANCELING:
                case COMPLETED:
                    break;
            }
        } catch (Exception e) {
                log.error("Error when sending cansel command: ", e);
                throw new RuntimeException(e);
        }
    }

    private void handleFault(ConditionCode conditionCode) {
        log.debug("TXID{} Handling fault {}", cfdpTransactionId, conditionCode);

        if (outTxState == OutTxState.CANCELING) {
            complete(conditionCode);
        } else {
            FaultHandlingAction action = getFaultHandlingAction(conditionCode);
            switch (action) {
            case ABANDON:
                complete(conditionCode);
                break;
            case CANCEL:
                cancel(conditionCode);
                break;
            case SUSPEND:
                suspend();
            }
        }
    }

    @Override
    public TransferDirection getDirection() {
        return TransferDirection.UPLOAD;
    }

    @Override
    public long getTotalSize() {
        return this.request.getFileLength();
    }

    @Override
    public String getBucketName() {
        return bucket != null ? bucket.getName() : null;
    }

    @Override
    public String getObjectName() {
        return request.getSourceFileName();
    }

    @Override
    public String getRemotePath() {
        return request.getDestinationFileName();
    }

    @Override
    public long getTransferredSize() {
        return this.transferred;
    }
}
