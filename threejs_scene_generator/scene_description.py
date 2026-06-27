from typing import Annotated, Literal

from pydantic import BaseModel, Field


class FogConfig(BaseModel):
    enabled: bool
    color: str
    near: float
    far: float


class Atmosphere(BaseModel):
    time_of_day: Literal["dawn", "morning", "midday", "dusk", "night"]
    sky: Annotated[list[str], Field(min_length=2, max_length=2)]
    fog: FogConfig
    light_temperature: Literal["warm", "neutral", "cool", "dramatic"]


class DepthLayer(BaseModel):
    layer: Literal["background", "midground", "foreground"]
    elements: list[str]


class SecondaryElement(BaseModel):
    name: str
    geometry: str
    color: str
    animation: str
    layer: Literal["background", "midground", "foreground"]


class Camera(BaseModel):
    position: Annotated[list[float], Field(min_length=3, max_length=3)]
    look_at: Annotated[list[float], Field(min_length=3, max_length=3)]
    fov: float


class SceneDescription(BaseModel):
    is_modification: bool
    hero_element: str
    hero_animation: Literal["drift", "orbit", "pulse", "sway", "rise"]
    atmosphere: Atmosphere
    depth_layers: Annotated[list[DepthLayer], Field(min_length=3, max_length=3)]
    secondary_elements: list[SecondaryElement]
    secondary_animations: list[str]
    camera: Camera
    palette: Annotated[list[str], Field(min_length=4, max_length=6)]
    scene_complexity: Literal["minimal", "medium", "rich"]
