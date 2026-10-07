from datetime import datetime
from decimal import Decimal
from typing import Annotated, Generic, Literal, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
Country = Annotated[str, StringConstraints(pattern=r"^[A-Z]{2}$")]
Currency = Annotated[str, StringConstraints(pattern=r"^[A-Z]{3}$")]
Mode = Literal["unspecified", "unrestricted", "required", "preferred"]
WorkArrangement = Literal["remote", "hybrid", "on_site"]
Contract = Literal["employee", "contractor", "self_employed", "other"]
T = TypeVar("T")


class Schema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Choice(Schema, Generic[T]):
    mode: Mode = "unspecified"
    values: list[T] = Field(default_factory=list, max_length=100)

    @model_validator(mode="after")
    def check_values(self):
        if self.mode in ("required", "preferred") and not self.values:
            raise ValueError("A required/preferred criterion needs at least one value")
        if self.mode in ("unspecified", "unrestricted") and self.values:
            raise ValueError("Unspecified/unrestricted criteria must not contain values")
        if len(set(self.values)) != len(self.values):
            raise ValueError("Duplicate criterion values")
        return self


class Location(Schema):
    country: Country | None = None
    region: Text | None = None
    city: Text | None = None
    commute_radius_km: int | None = Field(default=None, ge=0, le=1000)

    @model_validator(mode="after")
    def check_location(self):
        if (self.region or self.city or self.commute_radius_km is not None) and not self.country:
            raise ValueError("Country is required when supplying local location details")
        if self.commute_radius_km is not None and not self.city:
            raise ValueError("Commute radius requires a city")
        return self


class Authorization(Schema):
    country: Country
    status: Literal["authorized", "requires_sponsorship", "unknown"]


class Compensation(Schema):
    mode: Mode = "unspecified"
    accepted_currencies: list[Currency] = Field(default_factory=list, max_length=50)
    currency_basis: Literal["advertised", "actual_payment"] | None = None
    minimum: Decimal | None = Field(default=None, ge=0, allow_inf_nan=False)
    period: Literal["hour", "month", "year"] | None = None
    amount_basis: Literal["gross", "net", "unknown"] | None = None

    @model_validator(mode="after")
    def check_compensation(self):
        has_values = bool(self.accepted_currencies) or self.minimum is not None
        if self.mode in ("required", "preferred") and not has_values:
            raise ValueError("Compensation criterion requires currencies or minimum")
        if self.mode in ("unspecified", "unrestricted") and (
            has_values or self.currency_basis or self.period or self.amount_basis
        ):
            raise ValueError("Unspecified/unrestricted compensation cannot contain terms")
        if len(set(self.accepted_currencies)) != len(self.accepted_currencies):
            raise ValueError("Duplicate currencies")
        if self.accepted_currencies and not self.currency_basis:
            raise ValueError("Specify advertised versus actual payment currency")
        if self.minimum is not None and (
            len(self.accepted_currencies) != 1 or not self.period or not self.amount_basis
        ):
            raise ValueError("Minimum requires exactly one currency, period and gross/net basis")
        return self


class SkillEvidence(Schema):
    skill: Text
    experience_years: Decimal | None = Field(default=None, ge=0, le=100, allow_inf_nan=False)
    provenance: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]


class Pathway(Schema):
    id: Text
    label: Text
    search_scope: Literal["local", "national", "international", "selected_regions", "unspecified"] = "unspecified"
    location: Location = Field(default_factory=Location)
    work_countries: Choice[Country] = Field(default_factory=Choice[Country])
    work_arrangements: Choice[WorkArrangement] = Field(default_factory=Choice[WorkArrangement])
    relocation_allowed: bool | None = None
    relocation_conditions: Text | None = None
    travel_allowed: bool | None = None
    sponsorship: Choice[Literal["offered", "not_needed"]] = Field(default_factory=Choice[Literal["offered", "not_needed"]])
    authorizations: list[Authorization] = Field(default_factory=list, max_length=100)
    contracts: Choice[Contract] = Field(default_factory=Choice[Contract])
    compensation: Compensation = Field(default_factory=Compensation)

    @model_validator(mode="after")
    def check_authorizations(self):
        countries = [entry.country for entry in self.authorizations]
        if len(set(countries)) != len(countries):
            raise ValueError("Only one authorization declaration per country per pathway")
        if self.relocation_conditions and self.relocation_allowed is not True:
            raise ValueError("Relocation conditions require relocation_allowed=true")
        return self


class Preferences(Schema):
    current_location: Location = Field(default_factory=Location)
    employer_countries: Choice[Country] = Field(default_factory=Choice[Country])
    career_roles: Choice[Text] = Field(default_factory=Choice[Text])
    domains: Choice[Text] = Field(default_factory=Choice[Text])
    skill_evidence: list[SkillEvidence] = Field(default_factory=list, max_length=100)
    pathways: list[Pathway] = Field(default_factory=list, max_length=20)

    @model_validator(mode="after")
    def check_pathways(self):
        ids = [path.id for path in self.pathways]
        if len(set(ids)) != len(ids):
            raise ValueError("Pathway IDs must be unique")
        return self


class OwnerCreate(Schema):
    label: Text | None = None


class OwnerRead(OwnerCreate):
    id: UUID
    created_at: datetime


class ProfileCreate(Schema):
    label: Text
    preferences: Preferences


class ProfileUpdate(ProfileCreate):
    expected_version: int = Field(ge=1)


class VersionRead(Schema):
    id: UUID
    version: int
    schema_version: Literal[1]
    preferences: Preferences
    created_at: datetime


class ProfileRead(Schema):
    id: UUID
    owner_id: UUID
    label: Text
    created_at: datetime
    latest: VersionRead
