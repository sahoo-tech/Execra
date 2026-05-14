class ModeManager:
    # Handles Execra exe mode

    current_mode = "safe"
    
    @classmethod
    def switch_mode(cls, mode:str) -> None:
        # switch the current exe mode.

        cls.current_mode = mode

    @classmethod
    def get_mode(cls) -> str:
        # Getter for current/active exe mode
        
        return cls.current_mode