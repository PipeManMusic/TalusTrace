from talustrace.backend.models import Device, Side

class AutoSizer:
    """
    Calculates the dimensions of Device Boxes based on pin counts and labels.
    """
    GRID_SIZE = 20
    PIN_PITCH = 20
    CHAR_WIDTH = 8
    BOLD_CHAR_WIDTH = 9
    LABEL_HEIGHT_EST = 18
    ID_HEIGHT_EST = 14
    TEXT_PAD = 12
    PIN_TEXT_HEIGHT_EST = 14
    TEXT_INSET = 6

    @staticmethod
    def _estimate_text_width(text: str | None, bold: bool = False) -> int:
        length = len(text or "")
        base = length * (AutoSizer.BOLD_CHAR_WIDTH if bold else AutoSizer.CHAR_WIDTH)
        return max(base, 16)

    @staticmethod
    def _pin_text(pin) -> str:
        if pin.label and pin.label != pin.id:
            return f"{pin.id} {pin.label}"
        return str(pin.id)
    
    @staticmethod
    def calculate_size(device: Device) -> tuple[float, float]:
        """
        Returns (width, height) for the device box.
        """
        pins = device.pins if isinstance(device.pins, list) else []
        p_left = [p for p in pins if p.side == Side.LEFT]
        p_right = [p for p in pins if p.side == Side.RIGHT]
        p_top = [p for p in pins if p.side == Side.TOP]
        p_bottom = [p for p in pins if p.side == Side.BOTTOM]
        
        lr_max = max(len(p_left), len(p_right))
        tb_max = max(len(p_top), len(p_bottom))

        label_width_est = AutoSizer._estimate_text_width(device.label, bold=True)
        id_width_est = AutoSizer._estimate_text_width(f"({device.id})", bold=False)

        def max_text_width(pin_list):
            if not pin_list:
                return 0
            return max(AutoSizer._estimate_text_width(AutoSizer._pin_text(p)) for p in pin_list)

        left_text_w = max_text_width(p_left)
        right_text_w = max_text_width(p_right)
        top_text_w = max_text_width(p_top)
        bottom_text_w = max_text_width(p_bottom)

        # Horizontal sizing: account for label block plus left/right pin text with inset and a guard gap.
        text_inset = AutoSizer.TEXT_INSET
        horizontal_padding = 2 * AutoSizer.GRID_SIZE
        label_block_w = max(label_width_est, id_width_est)
        # Guard gap keeps long side labels from intruding into the centered label block.
        gap_between = max(AutoSizer.PIN_PITCH * 2, AutoSizer.TEXT_PAD + 12)

        side_text_left = left_text_w + text_inset
        side_text_right = right_text_w + text_inset
        label_guard_w = side_text_left + gap_between + label_block_w + gap_between + side_text_right

        raw_w_candidates = [
            label_block_w + horizontal_padding,
            left_text_w + right_text_w + (2 * text_inset) + AutoSizer.PIN_PITCH,
            label_guard_w,
            (tb_max * AutoSizer.PIN_PITCH) + horizontal_padding,
        ]
        if p_top:
            raw_w_candidates.append((top_text_w + AutoSizer.TEXT_PAD) * (len(p_top) + 1))
        if p_bottom:
            raw_w_candidates.append((bottom_text_w + AutoSizer.TEXT_PAD) * (len(p_bottom) + 1))

        raw_w = max(raw_w_candidates)

        # Vertical sizing: include top/bottom pin text plus centered label and side stacks.
        label_block = AutoSizer.LABEL_HEIGHT_EST + AutoSizer.ID_HEIGHT_EST + 12
        lr_span = (lr_max - 1) * AutoSizer.PIN_PITCH if lr_max > 0 else 0
        lr_block = lr_span + AutoSizer.PIN_TEXT_HEIGHT_EST

        top_block = (AutoSizer.PIN_PITCH + AutoSizer.PIN_TEXT_HEIGHT_EST + AutoSizer.TEXT_PAD) if p_top else 12
        bottom_block = (AutoSizer.PIN_PITCH + AutoSizer.PIN_TEXT_HEIGHT_EST + AutoSizer.TEXT_PAD) if p_bottom else 12

        center_block = max(label_block, lr_block, AutoSizer.PIN_PITCH)
        raw_h = top_block + center_block + bottom_block

        width = (int(raw_w / AutoSizer.GRID_SIZE) + 1) * AutoSizer.GRID_SIZE
        height = (int(raw_h / AutoSizer.GRID_SIZE) + 1) * AutoSizer.GRID_SIZE

        return width, height
