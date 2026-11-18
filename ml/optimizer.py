import pandas as pd
from typing import List, Dict, Any

class CinemaDeliveryOptimizer:
    """
    Intelligent Cinema Delivery Optimization & Advisory Engine.
    Provides automated, actionable risk mitigations for cinema operators,
    technical managers (TMS), and authorized KDM distribution partners.
    """

    @staticmethod
    def generate_recommendations(df: pd.DataFrame, recent_weeks: int = 4) -> List[Dict[str, Any]]:
        """
        Analyzes recent cinema screen delivery patterns and issues targeted operational advisories.
        """
        if df.empty:
            return []

        latest_week = df["time_step"].max()
        cutoff_week = max(1, latest_week - recent_weeks + 1)
        recent_df = df[df["time_step"] >= cutoff_week]

        recommendations = []

        # Group by screen to find active issues
        for screen, group in recent_df.groupby("cinema_screen"):
            latest_record = group.sort_values(by="time_step").iloc[-1]
            week = int(latest_record["time_step"])
            payment = int(latest_record["payment_completed"])
            kdm_avail = int(latest_record["kdm_available"])
            kdm_dec = int(latest_record["kdm_decryptable"])
            kdm_exp = int(latest_record["kdm_expired"])
            dcp_corr = float(latest_record["dcp_corruption_pct"])
            firmware = int(latest_record["firmware_update_required"])
            sound_sync = abs(float(latest_record["sound_sync_error_ms"]))
            net_delay = float(latest_record["network_delay_ms"])
            recovery_est = float(latest_record["recovery_time_min"])

            # 1. KDM Payment Pending & Issuance Risk
            if payment == 0:
                recommendations.append({
                    "screen": screen,
                    "week": week,
                    "category": "Licensing & Billing",
                    "severity": "CRITICAL" if kdm_avail == 0 else "WARNING",
                    "issue": f"Screen {screen}: Weekly distributor licensing payment is pending.",
                    "impact": "KDM key generation is blocked or will not be renewed for upcoming showtimes.",
                    "action": "Urgent financial clearance required. Cinema management must settle outstanding payment invoice and notify distributor booking desk to authorize automated KDM generation.",
                    "expected_recovery_time_min": recovery_est
                })

            # 2. KDM Decryption Failure / Broken Key
            if kdm_avail == 1 and kdm_dec == 0:
                recommendations.append({
                    "screen": screen,
                    "week": week,
                    "category": "Cryptographic Key Block",
                    "severity": "CRITICAL",
                    "issue": f"Screen {screen}: KDM is present on server but fails cryptographic decryption.",
                    "impact": "Server Integrated Media Block (IMB) cannot unlock MXF picture/sound essence. Ingest failure.",
                    "action": "Verify server certificate public key fingerprint. Request authorized KDM laboratory (Deluxe/Technicolor/Qube) to regenerate targeted KDM against cinema server certificate ID.",
                    "expected_recovery_time_min": recovery_est
                })

            # 3. KDM Expired or Imminent Expiry
            if kdm_exp == 1:
                recommendations.append({
                    "screen": screen,
                    "week": week,
                    "category": "Key Expiration",
                    "severity": "CRITICAL",
                    "issue": f"Screen {screen}: KDM validity license window has expired.",
                    "impact": "Content is rendered unplayable immediately.",
                    "action": "Submit extension request to distributor theatrical booking agent for an updated KDM key window covering remaining show schedule.",
                    "expected_recovery_time_min": recovery_est
                })

            # 4. DCP Corruption / Packet Loss
            if dcp_corr > 2.5:
                recommendations.append({
                    "screen": screen,
                    "week": week,
                    "category": "DCP Content Integrity",
                    "severity": "CRITICAL" if dcp_corr > 10.0 else "WARNING",
                    "issue": f"Screen {screen}: DCP package corruption detected ({dcp_corr}%).",
                    "impact": "Playback stutter, frame dropouts, or hash check failure on Theater Management System (TMS).",
                    "action": "Execute automated SHA-256 hash validation across all reel CPL/PKL manifests. Trigger delta re-transfer of corrupted MXF track files rather than downloading entire 150GB package.",
                    "expected_recovery_time_min": recovery_est
                })

            # 5. Firmware Update Required
            if firmware == 1:
                recommendations.append({
                    "screen": screen,
                    "week": week,
                    "category": "Hardware & Security Firmware",
                    "severity": "WARNING",
                    "issue": f"Screen {screen}: Server Media Block (IMB/SMS) requires mandatory firmware upgrade.",
                    "impact": "Potential security certificate handshake deprecation and playback lockouts.",
                    "action": "Schedule server firmware flash during non-operational off-hours (02:00 - 06:00). Conduct SMPTE 428 test pattern loop and Dolby/DTS audio pass prior to auditorium opening.",
                    "expected_recovery_time_min": recovery_est
                })

            # 6. Audio/Visual Synchronization Drift
            if sound_sync > 30.0:
                recommendations.append({
                    "screen": screen,
                    "week": week,
                    "category": "Audio/Visual Synchronization",
                    "severity": "WARNING",
                    "issue": f"Screen {screen}: Audio delay offset measured at {sound_sync:.1f} ms (SMPTE ST 428-1 tolerance is +/-20 ms).",
                    "impact": "Noticeable lip-sync lag or audio echo in auditorium seating.",
                    "action": "Calibrate auditorium sound processor delay buffer. In TMS projector profile, apply offset compensation of {-sound_sync:.1f} ms to realign AES3 audio output with DCI video stream.",
                    "expected_recovery_time_min": recovery_est
                })

            # 7. Network Latency / Multicast Delay
            if net_delay > 180.0:
                recommendations.append({
                    "screen": screen,
                    "week": week,
                    "category": "Transport Network Quality",
                    "severity": "WARNING",
                    "issue": f"Screen {screen}: High satellite/broadband delivery latency ({net_delay:.1f} ms).",
                    "impact": "Extended DCP ingest times and multicast packet drops.",
                    "action": "Switch TMS ingest interface to dedicated secondary Gigabit VLAN or utilize local edge cache server. Prioritize satellite multicast forward error correction (FEC).",
                    "expected_recovery_time_min": recovery_est
                })

        # Sort recommendations: CRITICAL first, then by estimated recovery time descending
        severity_order = {"CRITICAL": 0, "WARNING": 1, "INFO": 2}
        recommendations.sort(key=lambda r: (severity_order.get(r["severity"], 3), -r["expected_recovery_time_min"]))

        return recommendations
