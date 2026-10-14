
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AtencionCrear(BaseModel):
    estudiante_id: int = Field(gt=0)
    saturacion: int | None = Field(default=None, ge=0, le=100)
    frecuencia_cardiaca: int | None = Field(default=None, ge=0)
    temperatura: float | None = Field(default=None, ge=0)
    diagnostico_id: int = Field(gt=0)
    descripcion_diagnostico: str | None = None
    recomendacion: str | None = None

    @model_validator(mode="after")
    def validar_descripcion(self):
        descripcion = self.descripcion_diagnostico
        if descripcion is not None:
            descripcion = descripcion.strip()

        if descripcion == "":
            descripcion = None

        self.descripcion_diagnostico = descripcion

        return self


class AtencionRespuesta(BaseModel):
    id: int
    estudiante_id: int
    fecha_hora: datetime
    saturacion: int | None
    frecuencia_cardiaca: int | None
    temperatura: float | None
    diagnostico_id: int
    descripcion_diagnostico: str | None
    recomendacion: str | None
    usuario_id: int
    modificado_por: int | None = None
    fecha_modificacion: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class AtencionActualizar(BaseModel):
    saturacion: int | None = Field(ge=0, le=100)
    frecuencia_cardiaca: int | None = Field(ge=0)
    temperatura: float | None = Field(ge=0)
    diagnostico_id: int = Field(gt=0)
    descripcion_diagnostico: str | None = None
    recomendacion: str | None = None

    @model_validator(mode="after")
    def normalizar_descripcion(self):
        if self.descripcion_diagnostico is not None:
            self.descripcion_diagnostico = (
                self.descripcion_diagnostico.strip() or None
            )
        return self
