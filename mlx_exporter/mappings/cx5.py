from collections import OrderedDict

# Unit enable addresses in CR-space
# selector_addr = en_addr - 0x20
# value_addr    = en_addr + 0x20
UNITS = OrderedDict([
    ("TPT",  0x0a6620),  # Address translation caches
    ("PXT",  0x10faa0),  # PCIe interface
    ("RXB",  0x0dc420),  # RX packet buffer
    ("RXT",  0x05a220),  # RX steering
    ("RXW",  0x0650a0),  # Receive WQE handling
    ("RXS",  0x0749a0),  # RX packet scatter
    ("RXC",  0x086a20),  # Completion handling
    ("SXP",  0x0389a0),  # TX steering/packet
    ("SXW",  0x02cd20),  # TX descriptor handling
    ("SXD",  0x016820),  # TX scheduling/QoS
    ("RXPS", 0x043020),  # RX post-steering
    ("PXDP", 0x126420),  # PCIe data path
])
 
# Counter definitions: (unit, selector, metric_name, help, measurement)
# measurement: "events" or "cycles"
COUNTERS = [
    # TPT — Address Translation Caches
    ("TPT", 258, "mlx5_tpt_l0_mtt_hit", "Level 0 MTT cache hits", "events"),
    ("TPT", 257, "mlx5_tpt_l0_mtt_miss", "Level 0 MTT cache misses", "events"),
    ("TPT", 263, "mlx5_tpt_l1_mtt_hit", "Level 1 MTT cache hits", "events"),
    ("TPT", 262, "mlx5_tpt_l1_mtt_miss", "Level 1 MTT cache misses", "events"),
    ("TPT", 273, "mlx5_tpt_l0_mpt_hit", "Level 0 MPT cache hits", "events"),
    ("TPT", 272, "mlx5_tpt_l0_mpt_miss", "Level 0 MPT cache misses", "events"),
    ("TPT", 278, "mlx5_tpt_l1_mpt_hit", "Level 1 MPT cache hits", "events"),
    ("TPT", 277, "mlx5_tpt_l1_mpt_miss", "Level 1 MPT cache misses", "events"),
    ("TPT", 270, "mlx5_tpt_indirect_mem_key", "Indirect memory key accesses", "events"),
 
    # PXT — PCIe Interface
    ("PXT", 255, "mlx5_pxt_icm_cache_miss", "ICM cache misses (reads from host memory)", "events"),
    ("PXT", 399, "mlx5_pxt_pcie_internal_bp", "PCIe internal back pressure cycles", "cycles"),
    ("PXT", 423, "mlx5_pxt_outbound_stalled_reads", "Outbound stalled read cycles", "cycles"),
    ("PXT", 415, "mlx5_pxt_outbound_stalled_writes", "Outbound stalled write cycles", "cycles"),
    ("PXT", 263, "mlx5_pxt_read_stuck_no_engines", "PCIe read stalled no read engines", "cycles"),
    ("PXT", 271, "mlx5_pxt_read_stuck_byte_limit", "PCIe read stalled byte limit", "cycles"),
    ("PXT", 287, "mlx5_pxt_read_stuck_ordering", "PCIe read stalled ordering rules", "cycles"),
 
    # RXW — Receive WQE Handling
    ("RXW", 66, "mlx5_rxw_wqe_cache_hit", "Receive WQE cache hits", "events"),
    ("RXW", 65, "mlx5_rxw_wqe_cache_miss", "Receive WQE cache misses", "events"),
    ("RXW", 70, "mlx5_rxw_tpt_bp", "Back pressure from MMU to RX descriptor handling", "cycles"),
 
    # RXB — RX Packet Buffer
    ("RXB", 12, "mlx5_rxb_bw_64b_0", "RX packet buffer 64B units port 0", "events"),
    ("RXB", 13, "mlx5_rxb_packets_0", "RX packet buffer packets port 0", "events"),
    ("RXB", 9,  "mlx5_rxb_bw_64b_1", "RX packet buffer 64B units port 1", "events"),
    ("RXB", 10, "mlx5_rxb_packets_1", "RX packet buffer packets port 1", "events"),
    ("RXB", 52, "mlx5_rxb_rxs_no_credits", "Back pressure from scatter to RX buffer", "cycles"),
 
    # RXT — RX Steering
    ("RXT", 21, "mlx5_rxt_slice_load_slow", "RX packets that went through steering", "events"),
    ("RXT", 20, "mlx5_rxt_slice_load_fast", "RX packets that went through fast-path steering", "events"),

    # RXS — RX Packet Scatter
    ("RXS", 23, "mlx5_rxs_no_pxt_credits", "Back pressure from PCIe to packet scatter", "cycles"),
 
    # RXC — Completion Handling
    ("RXC", 104, "mlx5_rxc_eq_all_busy", "EQ all state machines busy cycles", "cycles"),
    ("RXC", 180, "mlx5_rxc_cq_all_busy", "CQ all state machines busy cycles", "cycles"),
    ("RXC", 43,  "mlx5_rxc_msix_all_busy", "MSI-X all state machines busy cycles", "cycles"),
    ("RXC", 227, "mlx5_rxc_cqe_compress_sessions", "CQE compression sessions", "events"),
 
    # SXW — TX Descriptor Handling
    ("SXW", 161, "mlx5_sxw_done_limited", "TX descriptor stopped limited state", "events"),
    ("SXW", 158, "mlx5_sxw_done_vl_limited", "TX descriptor stopped VL back pressure", "events"),
    ("SXW", 159, "mlx5_sxw_done_desched", "TX descriptor stopped de-schedule", "events"),
    ("SXW", 160, "mlx5_sxw_done_work_done", "TX descriptor stopped work done", "events"),
    ("SXW", 162, "mlx5_sxw_done_e2e_credits", "TX descriptor stopped E2E credits", "events"),
    ("SXW", 242, "mlx5_sxw_tx_packets", "TX packets", "events"),

    # SXP — TX Steering/Packet
    ("SXP", 139, "mlx5_sxp_line_port0", "Lines transmitted on port 0", "events"),
    ("SXP", 140, "mlx5_sxp_line_port1", "Lines transmitted on port 1", "events"),
    ("SXP", 141, "mlx5_sxp_line_loopback", "Loopback lines transmitted", "events"),
    ("SXP", 29, "mlx5_sxp_steering0_work_rate", "TX steering pipe 0 events", "events"),
    ("SXP", 27, "mlx5_sxp_steering1_work_rate", "TX steering pipe 1 events", "events"),
    ("SXP", 14, "mlx5_sxp_steering0_hit", "TX steering hits on pipe 0", "events"),
    ("SXP", 16, "mlx5_sxp_steering0_miss", "TX steering misses on pipe 0", "events"),
    ("SXP", 13, "mlx5_sxp_steering1_hit", "TX steering hits on pipe 1", "events"),
    ("SXP", 15, "mlx5_sxp_steering1_miss", "TX steering misses on pipe 1", "events"),
    ("SXP", 23, "mlx5_sxp_steering0_cache_miss", "TX steering rule-cache misses on pipe 0", "events"),
    ("SXP", 18, "mlx5_sxp_steering1_cache_miss", "TX steering rule-cache misses on pipe 1", "events"),
    ("SXP", 22, "mlx5_sxp_steering0_cache_total", "TX steering rule-cache accesses on pipe 0", "events"),
    ("SXP", 17, "mlx5_sxp_steering1_cache_total", "TX steering rule-cache accesses on pipe 1", "events"),

    # SXD — TX Scheduling
    # The original CX5 source excerpt used for this exporter does not define an
    # SXD selector in the active counter list, so leave SXD empty until verified.

    # RXPS — RX Post-Steering / Device
    ("RXPS", 0, "mlx5_device_clocks", "Chip frequency device clocks", "events"),
]
