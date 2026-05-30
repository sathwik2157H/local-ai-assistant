from enum import Enum, auto


class AssistantState(Enum):
    """
    Five distinct states that drive the orb's visual personality.
    Each state maps to a unique animation behavior and color identity.
    """
    IDLE      = auto()   # Calm, breathing presence — deep indigo
    LISTENING = auto()   # Attentive, expanding rings — electric cyan
    THINKING  = auto()   # Focused computation — violet aurora
    SPEAKING  = auto()   # Dynamic audio energy — warm amber
    ERROR     = auto()   # Urgent alert — sharp crimson
