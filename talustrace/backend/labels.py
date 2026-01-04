class LabelManager:
    """
    The 'Typing Copilot' that generates short-codes.
    """
    @staticmethod
    def generate_short_code(text: str) -> str:
        """
        Generates a short code from a longer string.
        e.g. "Coolant Temp" -> "CLNT_TMP"
        """
        vowels = "AEIOUaeiou"
        # Remove vowels, uppercase, replace spaces with underscores
        short = "".join(["_" if c.isspace() else c for c in text if c not in vowels]).upper()
        while "__" in short:
            short = short.replace("__", "_")
        return short[:8]  # Limit length
