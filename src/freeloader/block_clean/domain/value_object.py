class BlockId(str):
    def __new__(cls, value: str) -> "BlockId":
        if "." not in value:
            raise ValueError(
                f"Invalid block id '{value}', expected format 'provider.block'"
            )
        return str.__new__(cls, value)

    @property
    def provider(self) -> str:
        return self.split(".")[0]

    @property
    def block(self) -> str:
        return self.split(".")[1]

    @property
    def sub_path(self) -> str:
        return f"{self.provider}/{self.block}"
