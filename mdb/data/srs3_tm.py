from yamcs.pymdb import *
uint34_t = IntegerEncoding(
    bits=34,
    little_endian=False,
    scheme=IntegerEncodingScheme.TWOS_COMPLEMENT,
)
#　parameter
TM_list=[
    ["temp_mcu", int16_t, 0],
    ["temp_power", int16_t, 0],
    ["temp_lna", int16_t, 0],
    ["temp_pa", int16_t, 0],
    ["volt_vin", uint16_t, 0],
    ["volt_vreg", uint16_t, 0],
    ["volt_3v3", uint16_t, 0],
    ["curr_vin", int16_t, 0],
    ["curr_vreg", int16_t, 0],
    ["curr_3v3", int16_t, 0],
    ["power_vin", uint16_t, 0],
    ["power_vreg", uint16_t, 0],
    ["power_3v3", uint16_t, 0],

]

SYS_BOOT_COUNT_list=[
    ["boot_count",uint32_t,0]
]

SYS_GWDT_COUNTER_list=[
    ["gwdt_counter",uint32_t,0]
]

TX_list=[
    ["tx_allow_always", int8_t, 0],
    ["tx_allow_time", uint16_t, 0],
    ["tx_freq", uint32_t, 0],
    ["tx_rate", uint32_t, 0],
    ["tx_bt", uint8_t, 0],
    ["tx_pout", float32_t, 0],
    ["tx_gain", uint16_t, 0],
    ["tx_alc_mode", uint8_t, 0],
    ["tx_alc_kp", float32_t, 0],
    ["tx_alc_limit", uint16_t, 0],
    ["tx_alc_gain", uint16_t, 0],
    ["tx_rs", int8_t, 0],
    ["tx_cc", int8_t, 0],
    ["tx_rand", int8_t, 0],
    ["tx_crc", int8_t, 0],
    ["tx_idle_frames", uint16_t, 0],
    ["tx_train_type", uint8_t, 0],
    ["tx_preamble", uint16_t, 0],
    ["tx_postamble", uint16_t, 0],
    ["tx_midamble", uint16_t, 0],
    ["tx_size", uint16_t, 0],
    ["tx_id", uint16_t, 0],
    ["tx_crypto_key", uint34_t, 0], #Fix_length_34_t
    ["tx_crypto_encrypt", uint8_t, 0],
    ["tx_crypto_auth", uint8_t, 0],
    ["tx_frames", uint32_t, 0],
    ["tx_power_forward", float32_t, 0],
    ["tx_power_reflection", float32_t, 0],
    ["tx_over_power", uint16_t, 0],
    ["tx_pll_nolock", uint16_t, 0],

]

RX_list = [
    ["rx_freq", uint32_t, 0],
    ["rx_rate", uint32_t, 0],
    ["rx_bw", uint8_t, 0],
    ["rx_rs", uint8_t, 0],
    ["rx_cc", uint8_t, 0],
    ["rx_rand", uint8_t, 0],
    ["rx_crc", uint8_t, 0],
    ["rx_size", uint16_t, 0],
    ["rx_id", uint16_t, 0],
    ["rx_crypto_key", uint34_t, 0], #Fix_length_34_t
    ["rx_crypto_decrypt", uint8_t, 0],
    ["rx_crypto_auth", uint8_t, 0],
    ["rx_local_drop", uint8_t, 0],
    ["rx_frames", uint32_t, 0],
    ["rx_detected", uint32_t, 0],
    ["rx_rssi", float32_t, 0],
    ["rx_freqerr", float32_t, 0],
    ["rx_pll_nolock", uint16_t, 0],

]

# srs3
param_list=[
    ["TM",0x7495,TM_list],
    ["SYS_BOOT_COUNT",0x428c,SYS_BOOT_COUNT_list],
    ["SYS_GWDT_COUNTER",0x4290,SYS_GWDT_COUNTER_list],
    ["TX",0x11e4,TX_list],
    ["RX",0x4203,RX_list]
]
