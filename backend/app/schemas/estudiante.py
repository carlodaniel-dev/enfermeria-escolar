
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class EstudianteBase(BaseModel):
    nombre: str = Field(min_length=1, max_length=150)
    curso_id: int = Field(gt=0)
    paralelo_id: int | None = Field(default=None, gt=0)
    especialidad_id: int | None = Field(default=None, gt=0)
    sexo: Literal["Masculino", "Femenino"]

    @model_validator(mode="after")
    def validar_datos_academicos(self):
        if not self.nombre.strip():
            raise ValueError("El nombre es obligatorio.")

        if (
            self.paralelo_id is not None
            and self.especialidad_id is not None
        ):
            raise ValueError(
                "No se puede asignar paralelo y especialidad a la vez."
            )

        return self


class EstudianteCrear(EstudianteBase):
    pass


class EstudianteActualizar(EstudianteBase):
    pass


class EstudianteRespuesta(EstudianteBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
