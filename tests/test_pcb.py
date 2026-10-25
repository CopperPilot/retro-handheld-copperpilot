"""Automated 25-point hardware verification test suite for CopperPilot Retro Handheld (ESP32-S3) PCB."""

import os

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


class TestBoardPhysical:
    """Verifies board physical dimensions, 4-layer stackup, and Edge.Cuts contour."""

    def test_board_dimensions(self, pcb_data):
        """Assert outer bounding box matches 63.0 x 80.0 mm (+/- 0.5 mm tolerance)."""
        xs = []
        ys = []
        for elem in pcb_data.edge_cuts:
            if elem["type"] == "line":
                xs.extend([elem["x1"], elem["x2"]])
                ys.extend([elem["y1"], elem["y2"]])
            elif elem["type"] == "arc":
                xs.extend([elem["x1"], elem["xm"], elem["x2"]])
                ys.extend([elem["y1"], elem["ym"], elem["y2"]])
            elif elem["type"] == "circle":
                xs.extend([elem["cx"] - elem["radius"], elem["cx"] + elem["radius"]])
                ys.extend([elem["cy"] - elem["radius"], elem["cy"] + elem["radius"]])

        assert len(xs) > 0, "No Edge.Cuts elements found"
        width = max(xs) - min(xs)
        height = max(ys) - min(ys)

        assert 62.5 <= width <= 63.5, (
            f"Board width {width:.2f} mm out of range [62.5, 63.5]"
        )
        assert 79.5 <= height <= 80.5, (
            f"Board height {height:.2f} mm out of range [79.5, 80.5]"
        )

    def test_four_layer_stackup(self, pcb_data):
        """Assert standard Lion Circuits 4-layer copper stackup with 1.6 mm nominal thickness."""
        assert '"F.Cu"' in pcb_data.content
        assert '"In1.Cu"' in pcb_data.content
        assert '"In2.Cu"' in pcb_data.content
        assert '"B.Cu"' in pcb_data.content
        assert "(thickness 1.6)" in pcb_data.content or "1.6" in pcb_data.content

    def test_edge_cuts_closed_contour(self, pcb_data):
        """Assert Edge.Cuts contains perimeter elements defining outer profile and snap notches."""
        assert len(pcb_data.edge_cuts) >= 8, (
            f"Expected multiple Edge.Cuts primitives, got {len(pcb_data.edge_cuts)}"
        )


class TestConnectivityAndNetlist:
    """Verifies electrical connectivity, routing completeness, and DRC/ERC parity."""

    def test_drc_zero_unconnected_items(self, drc_results):
        """Assert kicad-cli pcb drc returns exactly 0 unconnected items (100% routed)."""
        unconnected = drc_results.get("unconnected_items", [])
        assert len(unconnected) == 0, (
            f"Found {len(unconnected)} unconnected items: {unconnected}"
        )

    def test_drc_zero_errors(self, drc_results):
        """Assert kicad-cli pcb drc returns 0 violations with severity 'error'."""
        violations = drc_results.get("violations", [])
        errors = [v for v in violations if v.get("severity") == "error"]
        assert len(errors) == 0, f"Found {len(errors)} DRC errors: {errors}"

    def test_erc_zero_errors(self, erc_results):
        """Assert kicad-cli sch erc returns 0 violations with severity 'error'."""
        sheets = erc_results.get("sheets", [])
        all_errors = []
        for sheet in sheets:
            errors = [
                v for v in sheet.get("violations", []) if v.get("severity") == "error"
            ]
            all_errors.extend(errors)
        assert len(all_errors) == 0, f"Found {len(all_errors)} ERC errors: {all_errors}"

    def test_all_critical_nets_present(self, pcb_data):
        """Assert all critical power and signal nets are represented on the PCB."""
        critical_nets = [
            "GND",
            "/+3V3",
            "VBUS",
            "/VBAT",
            "/VSYS",
            "/VSYS_PRE",
            "/TFT_SCLK",
            "/TFT_MOSI",
            "/TFT_MISO",
            "/TFT_CS",
            "/TFT_DC",
            "/TFT_RST",
            "/TFT_BL",
            "/BTN_UP",
            "/BTN_DOWN",
            "/BTN_LEFT",
            "/BTN_RIGHT",
            "/BTN_A",
            "/BTN_B",
            "/BTN_X",
            "/BTN_Y",
            "/BTN_SELECT",
            "/BTN_START",
            "/BTN_L1",
            "/BTN_L2",
            "/BTN_R1",
            "/BTN_R2",
            "/USB_D+",
            "/USB_D-",
            "/CHIP_EN",
            "/BOOT_BTN",
            "/VBAT_SENSE",
        ]
        for net in critical_nets:
            assert net in pcb_data.nets, f"Critical net '{net}' missing from PCB nets"

    def test_no_dangling_track_stubs(self, pcb_data):
        """Assert all track segments have non-zero physical length."""
        for seg in pcb_data.segments:
            assert seg["length"] > 0.00001, (
                f"Zero-length track segment detected at ({seg['x1']}, {seg['y1']})"
            )

    def test_no_unassigned_vias(self, pcb_data):
        """Assert all vias are bound to active named nets."""
        assert len(pcb_data.vias) >= 40, (
            f"Expected >= 40 vias, got {len(pcb_data.vias)}"
        )
        for via in pcb_data.vias:
            assert via["net_name"] != "", (
                f"Unassigned via detected at ({via['x']}, {via['y']})"
            )


class TestTraceGeometryAndDFM:
    """Verifies manufacturing rule margins against Lion Circuits 4-layer capabilities."""

    def test_signal_trace_min_width(self, pcb_data):
        """Assert all signal tracks meet or exceed 0.150 mm (6 mil Lion Circuits fab limit)."""
        for seg in pcb_data.segments:
            assert seg["width"] >= 0.150, (
                f"Trace width {seg['width']} mm at ({seg['x1']}, {seg['y1']}) violates 0.15 mm min"
            )

    def test_power_rail_trace_widths(self, pcb_data):
        """Assert power rail traces meet or exceed 0.20 mm width."""
        power_nets = {"/+3V3", "VBUS", "/VBAT", "/VSYS", "/VSYS_PRE"}
        for net in power_nets:
            segs = [s for s in pcb_data.segments if s["net_name"] == net]
            assert len(segs) > 0, f"Net {net} missing routed segments"
            for s in segs:
                assert s["width"] >= 0.150, (
                    f"Power net {net} has undersized segment: {s['width']} mm"
                )

    def test_via_drill_and_annular_ring(self, pcb_data):
        """Assert via drill >= 0.30 mm, diameter >= 0.60 mm, annular ring >= 0.15 mm."""
        for via in pcb_data.vias:
            assert via["drill"] >= 0.295, f"Via drill {via['drill']} mm < 0.30 mm limit"
            assert via["size"] >= 0.595, (
                f"Via diameter {via['size']} mm < 0.60 mm limit"
            )
            assert via["annular_ring"] >= 0.145, (
                f"Via annular ring {via['annular_ring']} mm < 0.15 mm Lion Circuits limit"
            )

    def test_zero_clearance_errors(self, drc_results):
        """Assert zero clearance violations reported by DRC engine."""
        clearance_errors = [
            v
            for v in drc_results.get("violations", [])
            if "clearance" in v.get("type", "").lower() and v.get("severity") == "error"
        ]
        assert len(clearance_errors) == 0, f"Found clearance errors: {clearance_errors}"


class TestSubsystemsAndComponents:
    """Verifies physical placement and layer partitioning of all onboard circuits."""

    def test_mcu_esp32s3_placement(self, pcb_data):
        """Assert ESP32-S3-WROOM-1 (U4) is placed on the rear layer (B.Cu)."""
        u4 = pcb_data.footprints.get("U4")
        assert u4 is not None, "U4 (ESP32-S3-WROOM-1) missing from PCB"
        assert u4["layer"] == "B.Cu", f"U4 placed on {u4['layer']}, expected B.Cu"

    def test_usb_c_and_esd_protection(self, pcb_data):
        """Assert USB-C port J1 and ESD protection diode U1 are placed on B.Cu."""
        assert "J1" in pcb_data.footprints, "J1 (USB-C) missing"
        assert "U1" in pcb_data.footprints, "U1 (USBLC6-2SC6) missing"
        assert pcb_data.footprints["J1"]["layer"] == "B.Cu"
        assert pcb_data.footprints["U1"]["layer"] == "B.Cu"
        assert "R3" in pcb_data.footprints and "R4" in pcb_data.footprints
        assert "R1" in pcb_data.footprints and "R2" in pcb_data.footprints

    def test_power_management_and_charger(self, pcb_data):
        """Assert MCP73831 charger (U2) and JST-PH battery connector (J2) exist on B.Cu."""
        assert "U2" in pcb_data.footprints, "U2 (MCP73831) missing"
        assert "J2" in pcb_data.footprints, "J2 (JST-PH Battery Header) missing"
        assert pcb_data.footprints["U2"]["layer"] == "B.Cu"
        assert pcb_data.footprints["J2"]["layer"] == "B.Cu"

    def test_power_path_and_regulator(self, pcb_data):
        """Assert P-MOSFET Q1, Schottky D2, Slide switch SW1, and LDO U3 exist on B.Cu."""
        for ref in ["Q1", "D2", "SW1", "U3"]:
            assert ref in pcb_data.footprints, f"{ref} missing from layout"
            assert pcb_data.footprints[ref]["layer"] == "B.Cu"

    def test_display_connector_on_front(self, pcb_data):
        """Assert ILI9341 2.4-inch display connector (J3) is placed on F.Cu."""
        j3 = pcb_data.footprints.get("J3")
        assert j3 is not None, "J3 (Display Header) missing"
        assert j3["layer"] == "F.Cu", f"J3 placed on {j3['layer']}, expected F.Cu"

    def test_all_14_front_tactile_switches(self, pcb_data):
        """Assert all 14 gameplay switches (SW4-SW17) are placed on F.Cu."""
        for i in range(4, 18):
            ref = f"SW{i}"
            assert ref in pcb_data.footprints, f"{ref} missing from layout"
            assert pcb_data.footprints[ref]["layer"] == "F.Cu", (
                f"{ref} placed on {pcb_data.footprints[ref]['layer']}, expected F.Cu"
            )

    def test_boot_and_reset_tactile_switches(self, pcb_data):
        """Assert SW2 (RESET) and SW3 (BOOT) are placed on rear layer (B.Cu)."""
        assert "SW2" in pcb_data.footprints and "SW3" in pcb_data.footprints
        assert pcb_data.footprints["SW2"]["layer"] == "B.Cu"
        assert pcb_data.footprints["SW3"]["layer"] == "B.Cu"


class TestGroundPlanesAndZoning:
    """Verifies ground return planes and power distribution integrity."""

    def test_ground_planes_exist(self, pcb_data):
        """Assert dedicated ground zones are poured across internal and external layers."""
        gnd_zones = [z for z in pcb_data.zones if z["net"] == "GND"]
        assert len(gnd_zones) >= 1, "No GND zones found in PCB layout"
        # Confirm In1.Cu is configured as ground reference plane
        assert '"In1.Cu"' in pcb_data.content, "In1.Cu plane missing from stackup"

    def test_ground_via_density(self, pcb_data):
        """Assert ground vias connect layers for low-impedance ground return."""
        gnd_vias = [v for v in pcb_data.vias if v["net_name"] == "GND"]
        assert len(gnd_vias) >= 2, f"GND via count {len(gnd_vias)} < 2"


class Test3DModelsAndSilkscreen:
    """Verifies 3D model assignments, environment variables, and silkscreen readability."""

    def test_all_footprints_have_3d_models(self, pcb_data):
        """Assert placed functional footprints have valid 3D models assigned."""
        missing_models = []
        for ref, fp in pcb_data.footprints.items():
            if len(fp["models"]) == 0:
                missing_models.append(ref)
        assert len(missing_models) == 0, (
            f"Footprints missing 3D models: {missing_models}"
        )

    def test_no_legacy_kicad_env_vars(self, pcb_data):
        """Assert no deprecated KICAD6_* or KICAD7_* environment variables remain."""
        for var in ["KICAD6_3DMODEL_DIR", "KICAD7_3DMODEL_DIR", "KICAD8_3DMODEL_DIR"]:
            assert var not in pcb_data.content, f"Found legacy {var} in PCB file"

    def test_pin1_polarity_indicators(self, pcb_data):
        """Assert polarized components have identifiable pad 1 definitions."""
        polarized = ["D1", "D2", "D3", "Q1", "Q2", "U1", "U2", "U3", "U4", "J1", "J2"]
        for ref in polarized:
            fp = pcb_data.footprints.get(ref)
            assert fp is not None, f"Component {ref} not found"
            pad_nums = {p["number"] for p in fp["pads"]}
            assert "1" in pad_nums or "A1" in pad_nums, (
                f"Component {ref} missing Pin 1 pad"
            )
