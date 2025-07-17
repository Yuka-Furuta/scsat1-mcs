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

import org.yamcs.tctm.csp.CspPacket;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;


public class Scsat1OutgoingTransfer extends Scsat1OngoingTransfer {
    private CspPacket cspFilePacket;
    private int sessionId;
    private byte[] fileSendPacket;
    private int fileSendPacketLength;
    private int offset;
    private int remainSize;

    private static final String STORAGE_NAME = "/storage/";
    private static final int CMD_OPEN = 2;
    private static final int CMD_DATA = 3;
    private static final int CMD_CLOSE = 4;
    private static final int MAX_FILENAME_BYTES = 64;
    private static final int MAX_DATA_BYTES = 200;

    private enum OutTxState {
        START,
        SENDING_DATA,
        CANCELING,
        COMPLETED
    }

    private Bucket bucket;
    private final int sleepBetweenPdus;

    private OutTxState outTxState;
    private long transferred;

    private boolean suspended = false;

    private PutRequest request;
    private ScheduledFuture<?> pduSendingSchedule;


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
        this.sessionId = (int) id;
        outTxState = OutTxState.START;
        this.sleepBetweenPdus = customPduDelay != null && customPduDelay > 0 ? customPduDelay
                : config.getInt("sleepBetweenPdus", 500);
    }

    private static CfdpTransactionId makeTransactionId(long sourceId, YConfiguration config, long id) {
        int seqNrSize = 2;
        long seqNum = id & ((1l << seqNrSize * 8) - 1);
        return new CfdpTransactionId(sourceId, seqNum);
    }

    /**
     * Start the transfer
     */
    public void start() {
        pduSendingSchedule = executor.scheduleAtFixedRate(this::sendPDU, 0, sleepBetweenPdus, TimeUnit.MILLISECONDS);
    }

    // Handles PDU sending based on the current transfer state.
    private void sendPDU() {
        if (suspended) {
            return;
        }
        try {
            switch (outTxState) {
                case START:
                    transferType = PredefinedTransferTypes.FILE_TRANSFER.toString();
                    uploadOpenCmd();
                    offset = 0;
                    transferred = 0;
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
                    break;

                default:
                    throw new IllegalStateException("unknown/illegal state");
            }
        }  catch (Exception e) {
                log.error("Error when sending command: ", e);
                throw new RuntimeException(e);
        }
    }

    // Concatenates two byte arrays into one.
    private byte[] concat(byte[] a, byte[] b) {
        ByteBuffer buf = ByteBuffer.allocate(a.length + b.length);
        buf.put(a).put(b);
        return buf.array();
    }

    // Create a header for a file packet with commandId and sessionId.
    public byte[] setFilePacketId(int commandId, int sessionId) {
        // command ID(1byte), session ID(2byte), sessionId is little-endian
        int commandSize = 1;
        int sessionIdSize = 2;
        ByteBuffer buf = ByteBuffer.allocate(1 + 2);
        buf.order(ByteOrder.LITTLE_ENDIAN);
        buf.put((byte) commandId).putShort((short) sessionId);
        return buf.array();
    }

    // Encode the file name in UTF-8 and pad to fixed length.
    private byte[] encodeFilename(String fileName) {
        byte[] raw = fileName.getBytes(StandardCharsets.UTF_8);
        if (raw.length > MAX_FILENAME_BYTES) {
            throw new IllegalArgumentException("filename too long");
        }
        ByteBuffer buf = ByteBuffer.allocate(MAX_FILENAME_BYTES);
        buf.put(raw);
        return buf.array();
    }
    // Create a binary chunk of file data with metadata.
    private byte[] encodeFileDataChunk(int offset, int sendFileSize, byte[] fileData) {
        // offset (4byte), sendFileSize (4byte), fileData（200byte）
        int offsetSize = 4;
        int sendFileSizeLength = 4;
        ByteBuffer buf = ByteBuffer.allocate(offsetSize + sendFileSizeLength + MAX_DATA_BYTES);
        buf.order(ByteOrder.LITTLE_ENDIAN);
        buf.putInt(offset).putInt(sendFileSize);
        int length = Math.min(fileData.length, MAX_DATA_BYTES);
        buf.put(fileData, 0, length);
        if (length < MAX_DATA_BYTES) {
            buf.put(new byte[MAX_DATA_BYTES - length]);
        }
        return buf.array();
    }

    private void sendFileCommand(byte[] data) throws IOException {
        int filePriority = 2;
        int fileDport = 13;
        int sourcePort = 32;
        ByteBuffer buf = ByteBuffer.allocate(4 + data.length);
        cspFilePacket = new CspPacket(buf);
        cspFilePacket.setHeader(
            (byte)filePriority,
            (byte)cfdpTransactionId.getInitiatorEntity(),
            (byte)request.getDestinationCfdpEntityId(),
            (byte)fileDport,
            (byte)sourcePort)
        ;
        buf.position(4);
        buf.put(data);
        fileSendPacket = cspFilePacket.getBytes();
        sendPacket(cfdpTransactionId, fileSendPacket);
    }

    private void uploadOpenCmd()  throws IOException {
        String fileName = STORAGE_NAME + request.getDestinationFileName();
        byte[] fileHeader = setFilePacketId(CMD_OPEN, sessionId);
        byte[] openFileName = encodeFilename(fileName);
        sendFileCommand(concat(fileHeader, openFileName));
    }

    private void uploadDataCmd()  throws IOException {
        int sendFileSize = 0; // uint32, little
        byte[] fileDataChunk; // binary, 1600bits
        byte[] uploadFileData;
        byte[] fileHeader = setFilePacketId(CMD_DATA, sessionId);
        if(remainSize == 0){
            if (offset % MAX_DATA_BYTES == 0){
                //  All data has been sent cleanly (no leftover bytes)
                offset = 0;
                sendFileSize = 0;
                fileDataChunk = new byte[0];
                uploadFileData = encodeFileDataChunk(offset, sendFileSize, fileDataChunk);
                sendFileCommand(concat(fileHeader, uploadFileData));
            }
            // Finalize the upload session 
            uploadCloseCmd(ConditionCode.NO_ERROR);
        } else {
            if (remainSize < MAX_DATA_BYTES){
                sendFileSize = remainSize;
            } else {
                sendFileSize = MAX_DATA_BYTES;
            }
            // Read a chunk of file data
            fileDataChunk = Arrays.copyOfRange(request.getFileData(), offset, offset + sendFileSize);
            // Encode and send the file chunk
            uploadFileData = encodeFileDataChunk(offset, sendFileSize, fileDataChunk);
            sendFileCommand(concat(fileHeader, uploadFileData));
            // Update offset and remaining size
            offset = offset + sendFileSize;
            remainSize = remainSize - sendFileSize;
            transferred = transferred + sendFileSize;
        }
    }

    private void uploadCloseCmd(ConditionCode conditionCode) throws IOException {
        byte[] fileHeader = setFilePacketId(CMD_CLOSE, sessionId);
        sendFileCommand(fileHeader);
        complete(conditionCode);
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

    @Override
    protected void suspend() {
        if (outTxState == OutTxState.COMPLETED) {
            log.info("TXID{} transfer finished, suspend ignored", cfdpTransactionId);
            return;
        }
        sendInfoEvent(ETYPE_TRANSFER_SUSPENDED, "transfer suspended");
        log.info("TXID{} suspending transfer", cfdpTransactionId);
        pduSendingSchedule.cancel(true);
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
        // Calculate elapsed time since the transfer started, in seconds
        long duration = (System.currentTimeMillis() - wallclockStartTime) / 1000;
        // State transition to COMPLETED
        String eventMessageSuffix = request.getSourceFileName() + " -> " + request.getDestinationFileName();
        if (conditionCode == ConditionCode.NO_ERROR) {
            changeState(TransferState.COMPLETED);
            sendInfoEvent(ETYPE_TRANSFER_FINISHED,
                    "transfer finished successfully in " + duration + " seconds: "
                            + eventMessageSuffix);
        } else {
            // Handle as error
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
                    suspended = false; // wake up if sleeping
                    outTxState = OutTxState.CANCELING;
                    changeState(TransferState.CANCELLING);
                    uploadCloseCmd(conditionCode);
                    break;
                case CANCELING:
                case COMPLETED:
                    break;
            }
        } catch (Exception e) {
                log.error("Error when sending cancel command: ", e);
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
