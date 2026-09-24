from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from app.schemas.rag import RAGCitation


class EpidemiologyData(BaseModel):
    global_incidence: Optional[str] = None
    mortality_rate: Optional[str] = None
    affected_regions: List[str] = Field(default_factory=list)
    outbreak_status: Optional[str] = None
    seasonal_pattern: Optional[str] = None
    high_risk_groups: List[str] = Field(default_factory=list)


class SpecialPopulationWarning(BaseModel):
    population: str
    warning: str
    recommendation: str


class DiseaseIntelligenceResponse(BaseModel):
    disease_name: str

    # Core overview
    summary: str
    pathophysiology: Optional[str] = None
    etiology: Optional[str] = None

    # Classification
    icd11_code: Optional[str] = None
    who_classification: Optional[str] = None
    disease_class: Optional[str] = None
    is_notifiable: bool = False
    is_outbreak_active: bool = False

    # Clinical features
    symptoms: List[str] = Field(default_factory=list)
    cardinal_symptoms: List[str] = Field(default_factory=list)
    signs_on_examination: List[str] = Field(default_factory=list)
    red_flags: List[str] = Field(default_factory=list)

    # Disease course
    incubation_period: Optional[str] = None
    disease_stages: List[str] = Field(default_factory=list)
    prognosis: Optional[str] = None
    complications: List[str] = Field(default_factory=list)

    # Management
    treatments: List[str] = Field(default_factory=list)
    first_line_treatment: Optional[str] = None
    medications: List[str] = Field(default_factory=list, description="Guideline-directed medications, dosages, and pharmacotherapy")
    investigations: List[str] = Field(default_factory=list)
    monitoring_parameters: List[str] = Field(default_factory=list)

    # Differential diagnosis
    differential_diagnosis_clues: List[str] = Field(default_factory=list)

    # Epidemiology
    epidemiology: Optional[EpidemiologyData] = None

    # Prevention and public health
    prevention: List[str] = Field(default_factory=list)
    public_health_measures: List[str] = Field(default_factory=list)

    # Special populations
    special_populations: List[SpecialPopulationWarning] = Field(default_factory=list)

    # Sources and citations
    citations: List[RAGCitation] = Field(default_factory=list)
    data_sources: List[str] = Field(default_factory=list)
    last_updated: Optional[str] = None
