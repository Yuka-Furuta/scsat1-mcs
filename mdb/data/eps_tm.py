from yamcs.pymdb import *

GENENAL_HK_TLM_list=[
    ["status", int8_t, 0],
    ["timestamp", "double_t", 0],
    ["uptime", uint32_t, 0],
    ["bootcount", uint32_t, 0],
    ["wdt_left", uint32_t, 0],
    ["wdt_count", uint32_t, 0],
    ["mppt_vol1", uint16_t, 0],
    ["mppt_vol2", uint16_t, 0],
    ["mppt_vol3", uint16_t, 0],
    ["mppt_vol4", uint16_t, 0],
    ["current_solar_panel1", uint16_t, 0],
    ["current_solar_panel2", uint16_t, 0],
    ["current_solar_panel3", uint16_t, 0],
    ["current_solar_panel4", uint16_t, 0],
    ["current_solar_panel5", uint16_t, 0],
    ["current_solar_panel6", uint16_t, 0],
    ["current_solar_panel7", uint16_t, 0],
    ["current_solar_panel8", uint16_t, 0],
    ["battery_voltage", uint16_t, 0],
    ["current_solar", uint16_t, 0],
    ["current_batt_in", uint16_t, 0],
    ["current_batt_out", uint16_t, 0],
    ["current_output1", uint16_t, 0],
    ["current_output2", uint16_t, 0],
    ["current_output3", uint16_t, 0],
    ["current_output4", uint16_t, 0],
    ["current_output5", uint16_t, 0],
    ["current_output6", uint16_t, 0],
    ["current_output7", uint16_t, 0],
    ["current_output8", uint16_t, 0],
    ["current_output9", uint16_t, 0],
    ["current_output10", uint16_t, 0],
    ["current_output11", uint16_t, 0],
    ["current_output12", uint16_t, 0],
    ["current_output13", uint16_t, 0],
    ["current_output14", uint16_t, 0],
    ["current_output15", uint16_t, 0],
    ["current_output16", uint16_t, 0],
    ["current_output17", uint16_t, 0],
    ["current_output18", uint16_t, 0],
    ["ao_current_output1", uint16_t, 0],
    ["ao_current_output2", uint16_t, 0],
    ["converter_vol1", uint16_t, 0],
    ["converter_vol2", uint16_t, 0],
    ["converter_vol3", uint16_t, 0],
    ["converter_vol4", uint16_t, 0],
    ["converter_vol5", uint16_t, 0],
    ["converter_vol6", uint16_t, 0],
    ["converter_vol7", uint16_t, 0],
    ["converter_vol8", uint16_t, 0],
    ["converter_state", uint8_t, 0],
    ["output_status1", uint1_t, 0],
    ["output_status2", uint1_t, 0],
    ["output_status3", uint1_t, 0],
    ["output_status4", uint1_t, 0],
    ["output_status5", uint1_t, 0],
    ["output_status6", uint1_t, 0],
    ["output_status7", uint1_t, 0],
    ["output_status8", uint1_t, 0],
    ["output_status9", uint1_t, 0],
    ["output_status10", uint1_t, 0],
    ["output_status11", uint1_t, 0],
    ["output_status12", uint1_t, 0],
    ["output_status13", uint1_t, 0],
    ["output_status14", uint1_t, 0],
    ["output_status15", uint1_t, 0],
    ["output_status16", uint1_t, 0],
    ["output_status17", uint1_t, 0],
    ["output_status18", uint1_t, 0],
    ["output_fault_status1", uint1_t, 0],
    ["output_fault_status2", uint1_t, 0],
    ["output_fault_status3", uint1_t, 0],
    ["output_fault_status4", uint1_t, 0],
    ["output_fault_status5", uint1_t, 0],
    ["output_fault_status6", uint1_t, 0],
    ["output_fault_status7", uint1_t, 0],
    ["output_fault_status8", uint1_t, 0],
    ["output_fault_status9", uint1_t, 0],
    ["output_fault_status10", uint1_t, 0],
    ["output_fault_status11", uint1_t, 0],
    ["output_fault_status12", uint1_t, 0],
    ["output_fault_status13", uint1_t, 0],
    ["output_fault_status14", uint1_t, 0],
    ["output_fault_status15", uint1_t, 0],
    ["output_fault_status16", uint1_t, 0],
    ["output_fault_status17", uint1_t, 0],
    ["output_fault_status18", uint1_t, 0],
    ["protected_access_count", uint16_t, 0],
    ["output_on_delta1", uint16_t, 0],
    ["output_on_delta2", uint16_t, 0],
    ["output_on_delta3", uint16_t, 0],
    ["output_on_delta4", uint16_t, 0],
    ["output_on_delta5", uint16_t, 0],
    ["output_on_delta6", uint16_t, 0],
    ["output_on_delta7", uint16_t, 0],
    ["output_on_delta8", uint16_t, 0],
    ["output_on_delta9", uint16_t, 0],
    ["output_on_delta10", uint16_t, 0],
    ["output_on_delta11", uint16_t, 0],
    ["output_on_delta12", uint16_t, 0],
    ["output_on_delta13", uint16_t, 0],
    ["output_on_delta14", uint16_t, 0],
    ["output_on_delta15", uint16_t, 0],
    ["output_on_delta16", uint16_t, 0],
    ["output_on_delta17", uint16_t, 0],
    ["output_on_delta18", uint16_t, 0],
    ["output_off_delta1", uint16_t, 0],
    ["output_off_delta2", uint16_t, 0],
    ["output_off_delta3", uint16_t, 0],
    ["output_off_delta4", uint16_t, 0],
    ["output_off_delta5", uint16_t, 0],
    ["output_off_delta6", uint16_t, 0],
    ["output_off_delta7", uint16_t, 0],
    ["output_off_delta8", uint16_t, 0],
    ["output_off_delta9", uint16_t, 0],
    ["output_off_delta10", uint16_t, 0],
    ["output_off_delta11", uint16_t, 0],
    ["output_off_delta12", uint16_t, 0],
    ["output_off_delta13", uint16_t, 0],
    ["output_off_delta14", uint16_t, 0],
    ["output_off_delta15", uint16_t, 0],
    ["output_off_delta16", uint16_t, 0],
    ["output_off_delta17", uint16_t, 0],
    ["output_off_delta18", uint16_t, 0],
    ["output_fault_count1", uint8_t, 0],
    ["output_fault_count2", uint8_t, 0],
    ["output_fault_count3", uint8_t, 0],
    ["output_fault_count4", uint8_t, 0],
    ["output_fault_count5", uint8_t, 0],
    ["output_fault_count6", uint8_t, 0],
    ["output_fault_count7", uint8_t, 0],
    ["output_fault_count8", uint8_t, 0],
    ["output_fault_count9", uint8_t, 0],
    ["output_fault_count10", uint8_t, 0],
    ["output_fault_count11", uint8_t, 0],
    ["output_fault_count12", uint8_t, 0],
    ["output_fault_count13", uint8_t, 0],
    ["output_fault_count14", uint8_t, 0],
    ["output_fault_count15", uint8_t, 0],
    ["output_fault_count16", uint8_t, 0],
    ["output_fault_count17", uint8_t, 0],
    ["output_fault_count18", uint8_t, 0],
    ["temperature1", int8_t, 0],
    ["temperature2", int8_t, 0],
    ["temperature3", int8_t, 0],
    ["temperature4", int8_t, 0],
    ["temperature5", int8_t, 0],
    ["temperature6", int8_t, 0],
    ["temperature7", int8_t, 0],
    ["temperature8", int8_t, 0],
    ["temperature9", int8_t, 0],
    ["temperature10", int8_t, 0],
    ["temperature11", int8_t, 0],
    ["temperature12", int8_t, 0],
    ["temperature13", int8_t, 0],
    ["temperature14", int8_t, 0],
    ["battery_status", uint8_t, 0],
    ["mppt_mode", uint8_t, 0],
    ["battery_heater_mode", uint8_t, 0],
    ["battery_heater_status", uint8_t, 0],
    ["ping_wdt_toggles", uint16_t, 0],
    ["ping_wdt_turn_offs", uint8_t, 0]


]
param_list=[
    ["GENENAL_HK_TLM",7,0,GENENAL_HK_TLM_list],
]
