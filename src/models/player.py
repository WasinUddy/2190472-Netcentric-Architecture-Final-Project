from pydantic import BaseModel, conlist, field_validator


class Player(BaseModel):
    name: str
    ships: conlist(int, min_length=16, max_length=16)
    radar_screen: conlist(int, min_length=64, max_length=64) = [0] * 64

    @field_validator('ships')
    def validate_state(cls, v):
        if len(set(v)) != len(v):
            raise ValueError('ship config must contain unique values')
        if any(value < 0 or value > 63 for value in v):
            raise ValueError('ship config values must be in the range 0-63')
        return v

    @field_validator('radar_screen', check_fields=False)
    def validate_screen(cls, v):
        if any(value < -1 or value > 1 for value in v):
            raise ValueError('game rendering value must be in the range -1 to 1')
        if v.count(1) > 16:
            raise ValueError(f'Too many ones in the game rendering; expected <= 16, got {v.count(1)}')
        return v
    