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
    protected DatagramSocket socket;
    protected int port;
    protected String host;
    protected InetAddress address;
    private byte[] sendData;
    private CspPacket cspFilePacket;
    private int sessionId = 0;
    private byte[] fileSendPacket;
    private int fileSendPacketLength;
    private int offset;
    private int remainSize;
    private final int sendDataMaxSize = 200;
    private static final String STORAGE_NAME = "/storage/";
    private static final int CMD_OPEN = 2;
    private static final int CMD_DATA = 3;
    private static final int CMD_CLOSE = 4;
    private static int seqNrSize = 4;
    private static int fileNameLength = 64;

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
        long seqNum = id & ((1l << seqNrSize * 8) - 1);
        return new CfdpTransactionId(sourceId, seqNum);
    }

    /**
     * Start the transfer
     */
    public void start() {
        // Configure the socket
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
                    uploadOpenCmd();
                    offset = 0;
                    remainSize = request.getFileLength();
                    this.outTxState = OutTxState.SENDING_DATA;
                    monitor.stateChanged(this);
                    break;
                case SENDING_DATA:
                    uploadDataCmd();
                    monitor.stateChanged(this);
                    break;
                case COMPLETED:
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

    // Concatenate ByteArrays
    public byte[] concat(byte[] a, byte[] b) {
        byte[] result = new byte[a.length + b.length];
        System.arraycopy(a, 0, result, 0, a.length);
        System.arraycopy(b, 0, result, a.length, b.length);
        return result;
    }

    public byte[] fileSendPacketHeader(int commandId, int sessionId) {
        //  1 byte: commandId, 2 bytes: sessionId (little-endian)
        int commandIdSize = 1;
        int sessionIdSize = 2;
        ByteBuffer buffer = ByteBuffer.allocate(commandIdSize + sessionIdSize);
        buffer.order(ByteOrder.LITTLE_ENDIAN);
        buffer.put((byte) commandId);
        buffer.putShort((short) sessionId);
        return buffer.array();
    }

    public byte[] fileName2ByteArray(String fileName) {
        ByteBuffer buffer = ByteBuffer.allocate(fileNameLength);
        byte[] fileNameBytes = fileName.getBytes(StandardCharsets.UTF_8);
        if (fileNameBytes.length > fileNameLength) {
            throw new IllegalArgumentException("fileName toofileSendPacketLength long (max" + fileNameLength + "bytes in UTF-8)");
        }
        buffer.put(fileNameBytes);
        // Filename is fixed, so pad with zeros
        buffer.put(new byte[fileNameLength - fileNameBytes.length]);
        return buffer.array();
    }

    public byte[] fileData2ByteArray(int offset, int sendFileSize, byte[] fileData) {
        // Allocate the required number of bytes
        int offsetSize = 4;
        int fileSizeLength = 4;
        ByteBuffer buffer = ByteBuffer.allocate(offsetSize + fileSizeLength + sendDataMaxSize);
        // Ensure fileData length does not exceed the maximum
        int fileDataLength = Math.min(fileData.length, sendDataMaxSize);
        // Little-endian
        buffer.order(ByteOrder.LITTLE_ENDIAN);
        buffer.putInt(offset);
        buffer.putInt(sendFileSize);
        buffer.put(fileData, 0, fileDataLength);
        //  Pad missing bytes with zeros for transmission
        if (fileDataLength < sendDataMaxSize) {
            buffer.put(new byte[sendDataMaxSize - fileDataLength]);
        }
        return buffer.array();
    }

    // Setup socket and address
    public void setUdpSender() throws SocketException, UnknownHostException {
        socket = new DatagramSocket();
        address = InetAddress.getByName(host);
    }

    // public static void printHex(byte[] data) {
    //     for (byte b : data) {
    //         System.out.printf("%02X ", b); // 2桁の16進数、先頭にゼロ埋め
    //     }
    //     System.out.println();
    // }


    public void sendFileCommand(byte[] data) throws IOException {
        int headerSize = 4;
        ByteBuffer buf = ByteBuffer.allocate(headerSize + data.length);
        cspFilePacket = new CspPacket(buf);
        int filePriority = 2;
        byte src = (byte) cfdpTransactionId.getInitiatorEntity();
        byte dst = (byte) request.getDestinationCfdpEntityId();
        int fileDport = 13;
        cspFilePacket.setHeader((byte)filePriority, src, dst, (byte)fileDport, (byte)32);
        // Write data after the header
        buf.position(headerSize);
        buf.put(data);
        fileSendPacket = cspFilePacket.getBytes();
        fileSendPacketLength = cspFilePacket.getLength();
        DatagramPacket packet = new DatagramPacket(fileSendPacket, fileSendPacketLength, address, port);
        socket.send(packet);
    }

    // Series of command transmissions
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
                // Send completion notification when exactly sent
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
            // Read chunk data of given size
            fileDataChunk = Arrays.copyOfRange(request.getFileData(), offset, offset + sendFileSize);
            // Send a packet
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
        // Calculate elapsed time since transfer start in seconds
        long duration = (System.currentTimeMillis() - wallclockStartTime) / 1000;
        // Send success message as INFO event, change state to COMPLETED
        String eventMessageSuffix = request.getSourceFileName() + " -> " + request.getDestinationFileName();
        if (conditionCode == ConditionCode.NO_ERROR) {
            changeState(TransferState.COMPLETED);
            sendInfoEvent(ETYPE_TRANSFER_FINISHED,
                    "transfer finished successfully in " + duration + " seconds: "
                            + eventMessageSuffix);
        } else {
            // Handle as error , send details as a warning event
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
