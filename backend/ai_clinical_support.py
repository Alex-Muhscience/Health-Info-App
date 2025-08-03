"""
AI-Powered Clinical Decision Support System
Advanced machine learning for diagnosis assistance, drug interactions, and treatment recommendations
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import uuid
import re
from sqlalchemy import and_, or_, func
from backend.database import db
from backend.models import Client, Visit, Prescription, LabOrder, MedicalRecord
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import logging

# Configure AI clinical logger
ai_clinical_logger = logging.getLogger('ai_clinical')

class RecommendationConfidence(Enum):
    """Confidence levels for AI recommendations"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"

class InteractionSeverity(Enum):
    """Drug interaction severity levels"""
    MINOR = "minor"
    MODERATE = "moderate"
    MAJOR = "major"
    CONTRAINDICATED = "contraindicated"

class DiagnosisCategory(Enum):
    """Medical diagnosis categories"""
    CARDIOVASCULAR = "cardiovascular"
    RESPIRATORY = "respiratory"
    GASTROINTESTINAL = "gastrointestinal"
    NEUROLOGICAL = "neurological"
    ENDOCRINE = "endocrine"
    INFECTIOUS = "infectious"
    DERMATOLOGICAL = "dermatological"
    MUSCULOSKELETAL = "musculoskeletal"
    PSYCHIATRIC = "psychiatric"
    OTHER = "other"

@dataclass
class DrugInfo:
    """Comprehensive drug information"""
    name: str
    generic_name: str
    brand_names: List[str]
    drug_class: List[str]
    indications: List[str]
    contraindications: List[str]
    side_effects: List[str]
    dosage_forms: List[str]
    typical_dosages: Dict[str, str]
    pregnancy_category: Optional[str]
    controlled_substance: bool
    black_box_warning: Optional[str]
    monitoring_requirements: List[str]
    renal_adjustment: bool
    hepatic_adjustment: bool
    half_life: Optional[str]

@dataclass
class DrugInteraction:
    """Drug-drug interaction information"""
    drug1: str
    drug2: str
    severity: InteractionSeverity
    mechanism: str
    clinical_effect: str
    management: str
    evidence_level: str
    frequency: str
    onset: str
    documentation: str

@dataclass
class ClinicalRecommendation:
    """AI-generated clinical recommendation"""
    id: str
    patient_id: str
    recommendation_type: str
    title: str
    description: str
    rationale: str
    confidence: RecommendationConfidence
    evidence_sources: List[str]
    action_required: bool
    priority: int
    created_at: datetime
    expires_at: Optional[datetime] = None
    acknowledged: bool = False

@dataclass
class DiagnosticSuggestion:
    """AI diagnostic suggestion"""
    diagnosis: str
    icd10_code: Optional[str]
    category: DiagnosisCategory
    probability: float
    supporting_evidence: List[str]
    recommended_tests: List[str]
    differential_diagnoses: List[str]
    clinical_notes: str

class DrugDatabase:
    """Comprehensive drug database with interaction checking"""
    
    def __init__(self):
        self.drugs: Dict[str, DrugInfo] = {}
        self.interactions: List[DrugInteraction] = []
        self._initialize_drug_database()
        self._initialize_interactions()
    
    def _initialize_drug_database(self):
        """Initialize comprehensive drug database"""
        
        # Common medications database (sample data)
        drugs_data = [
            {
                "name": "metformin",
                "generic_name": "metformin",
                "brand_names": ["Glucophage", "Fortamet", "Glumetza"],
                "drug_class": ["biguanides", "antidiabetic"],
                "indications": ["type 2 diabetes", "PCOS", "prediabetes"],
                "contraindications": ["renal impairment", "metabolic acidosis", "severe infection"],
                "side_effects": ["nausea", "diarrhea", "metallic taste", "lactic acidosis (rare)"],
                "dosage_forms": ["tablet", "extended-release tablet", "solution"],
                "typical_dosages": {
                    "initial": "500mg twice daily",
                    "maintenance": "1000-2000mg daily",
                    "maximum": "2550mg daily"
                },
                "pregnancy_category": "B",
                "controlled_substance": False,
                "black_box_warning": "Lactic acidosis risk",
                "monitoring_requirements": ["renal function", "vitamin B12", "lactic acid"],
                "renal_adjustment": True,
                "hepatic_adjustment": False,
                "half_life": "4-6 hours"
            },
            {
                "name": "lisinopril",
                "generic_name": "lisinopril",
                "brand_names": ["Prinivil", "Zestril"],
                "drug_class": ["ACE inhibitor", "antihypertensive"],
                "indications": ["hypertension", "heart failure", "post-MI"],
                "contraindications": ["angioedema", "pregnancy", "bilateral renal artery stenosis"],
                "side_effects": ["dry cough", "hyperkalemia", "angioedema", "hypotension"],
                "dosage_forms": ["tablet"],
                "typical_dosages": {
                    "initial": "10mg daily",
                    "maintenance": "20-40mg daily",
                    "maximum": "80mg daily"
                },
                "pregnancy_category": "D",
                "controlled_substance": False,
                "black_box_warning": "Fetal toxicity",
                "monitoring_requirements": ["blood pressure", "renal function", "potassium"],
                "renal_adjustment": True,
                "hepatic_adjustment": False,
                "half_life": "12 hours"
            },
            {
                "name": "warfarin",
                "generic_name": "warfarin",
                "brand_names": ["Coumadin", "Jantoven"],
                "drug_class": ["anticoagulant", "vitamin K antagonist"],
                "indications": ["atrial fibrillation", "DVT", "PE", "mechanical heart valves"],
                "contraindications": ["active bleeding", "pregnancy", "severe liver disease"],
                "side_effects": ["bleeding", "bruising", "hair loss", "skin necrosis"],
                "dosage_forms": ["tablet"],
                "typical_dosages": {
                    "initial": "5-10mg daily",
                    "maintenance": "2-10mg daily (INR guided)",
                    "maximum": "varies by indication"
                },
                "pregnancy_category": "X",
                "controlled_substance": False,
                "black_box_warning": "Bleeding risk",
                "monitoring_requirements": ["INR", "CBC", "signs of bleeding"],
                "renal_adjustment": False,
                "hepatic_adjustment": True,
                "half_life": "20-60 hours"
            }
        ]
        
        for drug_data in drugs_data:
            drug = DrugInfo(**drug_data)
            self.drugs[drug.name.lower()] = drug
            # Also index by brand names
            for brand in drug.brand_names:
                self.drugs[brand.lower()] = drug
    
    def _initialize_interactions(self):
        """Initialize drug interaction database"""
        
        interactions_data = [
            {
                "drug1": "warfarin",
                "drug2": "aspirin",
                "severity": InteractionSeverity.MAJOR,
                "mechanism": "Additive anticoagulant effects",
                "clinical_effect": "Increased bleeding risk",
                "management": "Monitor INR closely, consider PPI, watch for bleeding",
                "evidence_level": "Well-documented",
                "frequency": "Common",
                "onset": "Rapid",
                "documentation": "Established"
            },
            {
                "drug1": "metformin",
                "drug2": "contrast media",
                "severity": InteractionSeverity.MODERATE,
                "mechanism": "Renal impairment potentiation",
                "clinical_effect": "Increased lactic acidosis risk",
                "management": "Hold metformin 48h before and after contrast",
                "evidence_level": "Well-documented",
                "frequency": "Uncommon",
                "onset": "Delayed",
                "documentation": "Established"
            },
            {
                "drug1": "lisinopril",
                "drug2": "potassium supplements",
                "severity": InteractionSeverity.MODERATE,
                "mechanism": "Additive potassium retention",
                "clinical_effect": "Hyperkalemia",
                "management": "Monitor potassium levels, reduce K+ supplements",
                "evidence_level": "Well-documented",
                "frequency": "Common",
                "onset": "Delayed",
                "documentation": "Established"
            }
        ]
        
        self.interactions = [DrugInteraction(**interaction) for interaction in interactions_data]
    
    def search_drug(self, drug_name: str) -> Optional[DrugInfo]:
        """Search for drug information"""
        return self.drugs.get(drug_name.lower())
    
    def check_interactions(self, medications: List[str]) -> List[DrugInteraction]:
        """Check for drug interactions"""
        found_interactions = []
        
        # Normalize medication names
        normalized_meds = [med.lower().strip() for med in medications]
        
        for interaction in self.interactions:
            drug1_lower = interaction.drug1.lower()
            drug2_lower = interaction.drug2.lower()
            
            if drug1_lower in normalized_meds and drug2_lower in normalized_meds:
                found_interactions.append(interaction)
        
        return found_interactions
    
    def get_contraindications(self, drug_name: str, patient_conditions: List[str]) -> List[str]:
        """Check for contraindications based on patient conditions"""
        drug = self.search_drug(drug_name)
        if not drug:
            return []
        
        contraindications = []
        patient_conditions_lower = [cond.lower() for cond in patient_conditions]
        
        for contraindication in drug.contraindications:
            for condition in patient_conditions_lower:
                if condition in contraindication.lower():
                    contraindications.append(contraindication)
        
        return contraindications

class AIPatternRecognition:
    """AI pattern recognition for clinical insights"""
    
    def __init__(self):
        self.symptom_vectorizer = TfidfVectorizer(stop_words='english', max_features=1000)
        self.diagnosis_patterns = self._load_diagnosis_patterns()
    
    def _load_diagnosis_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Load diagnosis patterns and associated symptoms"""
        
        return {
            "diabetes_type_2": {
                "symptoms": ["polyuria", "polydipsia", "weight loss", "fatigue", "blurred vision"],
                "lab_findings": ["elevated glucose", "elevated HbA1c"],
                "risk_factors": ["obesity", "family history", "sedentary lifestyle"],
                "category": DiagnosisCategory.ENDOCRINE,
                "icd10": "E11"
            },
            "hypertension": {
                "symptoms": ["headache", "dizziness", "chest pain", "shortness of breath"],
                "lab_findings": ["elevated blood pressure"],
                "risk_factors": ["age", "obesity", "smoking", "family history"],
                "category": DiagnosisCategory.CARDIOVASCULAR,
                "icd10": "I10"
            },
            "pneumonia": {
                "symptoms": ["fever", "cough", "chest pain", "shortness of breath", "fatigue"],
                "lab_findings": ["elevated WBC", "chest x-ray infiltrates"],
                "risk_factors": ["age", "immunocompromised", "chronic lung disease"],
                "category": DiagnosisCategory.RESPIRATORY,
                "icd10": "J18"
            },
            "depression": {
                "symptoms": ["sadness", "loss of interest", "fatigue", "sleep disturbance", "appetite changes"],
                "lab_findings": [],
                "risk_factors": ["family history", "trauma", "chronic illness", "substance abuse"],
                "category": DiagnosisCategory.PSYCHIATRIC,
                "icd10": "F32"
            }
        }
    
    def suggest_diagnoses(
        self, 
        symptoms: List[str], 
        lab_results: List[str] = None,
        patient_history: List[str] = None
    ) -> List[DiagnosticSuggestion]:
        """Suggest possible diagnoses based on symptoms and findings"""
        
        suggestions = []
        lab_results = lab_results or []
        patient_history = patient_history or []
        
        # Combine all clinical information
        clinical_text = " ".join(symptoms + lab_results + patient_history).lower()
        
        for diagnosis, pattern in self.diagnosis_patterns.items():
            score = self._calculate_diagnosis_score(
                clinical_text, pattern, symptoms, lab_results, patient_history
            )
            
            if score > 0.3:  # Threshold for relevance
                suggestion = DiagnosticSuggestion(
                    diagnosis=diagnosis.replace("_", " ").title(),
                    icd10_code=pattern.get("icd10"),
                    category=pattern["category"],
                    probability=min(score, 0.95),  # Cap at 95%
                    supporting_evidence=self._get_supporting_evidence(
                        pattern, symptoms, lab_results
                    ),
                    recommended_tests=self._get_recommended_tests(diagnosis),
                    differential_diagnoses=self._get_differential_diagnoses(diagnosis),
                    clinical_notes=self._generate_clinical_notes(pattern, score)
                )
                suggestions.append(suggestion)
        
        # Sort by probability
        suggestions.sort(key=lambda x: x.probability, reverse=True)
        return suggestions[:5]  # Return top 5 suggestions
    
    def _calculate_diagnosis_score(
        self, 
        clinical_text: str, 
        pattern: Dict[str, Any],
        symptoms: List[str],
        lab_results: List[str],
        patient_history: List[str]
    ) -> float:
        """Calculate diagnostic probability score"""
        
        score = 0.0
        
        # Symptom matching (40% weight)
        symptom_matches = 0
        for pattern_symptom in pattern["symptoms"]:
            if pattern_symptom.lower() in clinical_text:
                symptom_matches += 1
        
        if pattern["symptoms"]:
            symptom_score = symptom_matches / len(pattern["symptoms"])
            score += symptom_score * 0.4
        
        # Lab finding matching (35% weight)
        lab_matches = 0
        for lab_finding in pattern["lab_findings"]:
            if lab_finding.lower() in clinical_text:
                lab_matches += 1
        
        if pattern["lab_findings"]:
            lab_score = lab_matches / len(pattern["lab_findings"])
            score += lab_score * 0.35
        
        # Risk factor matching (25% weight)
        risk_matches = 0
        for risk_factor in pattern["risk_factors"]:
            if risk_factor.lower() in clinical_text:
                risk_matches += 1
        
        if pattern["risk_factors"]:
            risk_score = risk_matches / len(pattern["risk_factors"])
            score += risk_score * 0.25
        
        return score
    
    def _get_supporting_evidence(
        self, 
        pattern: Dict[str, Any], 
        symptoms: List[str], 
        lab_results: List[str]
    ) -> List[str]:
        """Get supporting evidence for diagnosis"""
        
        evidence = []
        
        # Check for matching symptoms
        for symptom in symptoms:
            for pattern_symptom in pattern["symptoms"]:
                if pattern_symptom.lower() in symptom.lower():
                    evidence.append(f"Symptom: {symptom}")
        
        # Check for matching lab results
        for lab in lab_results:
            for pattern_lab in pattern["lab_findings"]:
                if pattern_lab.lower() in lab.lower():
                    evidence.append(f"Lab finding: {lab}")
        
        return evidence
    
    def _get_recommended_tests(self, diagnosis: str) -> List[str]:
        """Get recommended tests for diagnosis"""
        
        test_recommendations = {
            "diabetes_type_2": ["HbA1c", "fasting glucose", "oral glucose tolerance test"],
            "hypertension": ["ECG", "echocardiogram", "renal function tests"],
            "pneumonia": ["chest X-ray", "CBC with differential", "blood cultures"],
            "depression": ["PHQ-9", "thyroid function", "vitamin B12"]
        }
        
        return test_recommendations.get(diagnosis, [])
    
    def _get_differential_diagnoses(self, diagnosis: str) -> List[str]:
        """Get differential diagnoses"""
        
        differentials = {
            "diabetes_type_2": ["Type 1 diabetes", "MODY", "secondary diabetes"],
            "hypertension": ["white coat hypertension", "secondary hypertension"],
            "pneumonia": ["bronchitis", "COPD exacerbation", "pulmonary embolism"],
            "depression": ["bipolar disorder", "anxiety disorder", "thyroid disorder"]
        }
        
        return differentials.get(diagnosis, [])
    
    def _generate_clinical_notes(self, pattern: Dict[str, Any], score: float) -> str:
        """Generate clinical notes for diagnosis suggestion"""
        
        confidence = "high" if score > 0.7 else "moderate" if score > 0.5 else "low"
        
        return (f"AI diagnostic suggestion with {confidence} confidence based on "
                f"symptom pattern recognition and clinical decision support algorithms.")

class ClinicalDecisionEngine:
    """Main clinical decision support engine"""
    
    def __init__(self):
        self.drug_database = DrugDatabase()
        self.pattern_recognition = AIPatternRecognition()
        self.active_recommendations: Dict[str, List[ClinicalRecommendation]] = {}
    
    def analyze_patient(self, patient_id: str) -> Dict[str, Any]:
        """Comprehensive patient analysis with AI recommendations"""
        
        # Get patient data
        patient = db.session.query(Client).filter(Client.id == patient_id).first()
        if not patient:
            return {"error": "Patient not found"}
        
        # Get recent visits and symptoms
        recent_visits = db.session.query(Visit).filter(
            Visit.client_id == patient_id,
            Visit.visit_date >= datetime.utcnow() - timedelta(days=90)
        ).order_by(Visit.visit_date.desc()).all()
        
        # Extract symptoms and clinical information
        symptoms = []
        diagnoses = []
        for visit in recent_visits:
            if visit.purpose:
                symptoms.extend(visit.purpose.split(','))
            if visit.diagnosis:
                diagnoses.append(visit.diagnosis)
        
        # Get current medications
        current_meds = db.session.query(Prescription).filter(
            Prescription.client_id == patient_id,
            Prescription.status == 'active'
        ).all()
        
        medications = [med.medication_name for med in current_meds]
        
        # Get lab results
        recent_labs = db.session.query(LabOrder).filter(
            LabOrder.client_id == patient_id,
            LabOrder.result_date >= datetime.utcnow() - timedelta(days=180),
            LabOrder.result_value.isnot(None)
        ).all()
        
        lab_results = [
            f"{lab.test.name if lab.test else 'Unknown'}: {lab.result_value}"
            for lab in recent_labs
        ]
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            patient_id, symptoms, medications, lab_results, diagnoses
        )
        
        # Store recommendations
        self.active_recommendations[patient_id] = recommendations
        
        return {
            "patient_id": patient_id,
            "analysis_date": datetime.utcnow().isoformat(),
            "diagnostic_suggestions": self.pattern_recognition.suggest_diagnoses(
                symptoms, lab_results, diagnoses
            ),
            "drug_interactions": self.drug_database.check_interactions(medications),
            "clinical_recommendations": recommendations,
            "medication_review": self._review_medications(medications, patient),
            "risk_assessment": self._assess_patient_risk(patient, recent_visits)
        }
    
    def _generate_recommendations(
        self,
        patient_id: str,
        symptoms: List[str],
        medications: List[str],
        lab_results: List[str],
        diagnoses: List[str]
    ) -> List[ClinicalRecommendation]:
        """Generate clinical recommendations"""
        
        recommendations = []
        
        # Drug interaction recommendations
        interactions = self.drug_database.check_interactions(medications)
        for interaction in interactions:
            if interaction.severity in [InteractionSeverity.MAJOR, InteractionSeverity.CONTRAINDICATED]:
                recommendations.append(ClinicalRecommendation(
                    id=str(uuid.uuid4()),
                    patient_id=patient_id,
                    recommendation_type="drug_interaction",
                    title=f"Drug Interaction: {interaction.drug1} + {interaction.drug2}",
                    description=interaction.clinical_effect,
                    rationale=interaction.mechanism,
                    confidence=RecommendationConfidence.HIGH,
                    evidence_sources=[interaction.documentation],
                    action_required=True,
                    priority=1 if interaction.severity == InteractionSeverity.CONTRAINDICATED else 2,
                    created_at=datetime.utcnow()
                ))
        
        # Preventive care recommendations
        preventive_recs = self._generate_preventive_care_recommendations(patient_id)
        recommendations.extend(preventive_recs)
        
        # Monitoring recommendations
        monitoring_recs = self._generate_monitoring_recommendations(medications)
        recommendations.extend(monitoring_recs)
        
        return recommendations
    
    def _generate_preventive_care_recommendations(self, patient_id: str) -> List[ClinicalRecommendation]:
        """Generate preventive care recommendations"""
        
        recommendations = []
        patient = db.session.query(Client).filter(Client.id == patient_id).first()
        
        if not patient or not patient.dob:
            return recommendations
        
        age = (datetime.utcnow().date() - patient.dob).days // 365
        
        # Age-based screening recommendations
        if age >= 50:
            recommendations.append(ClinicalRecommendation(
                id=str(uuid.uuid4()),
                patient_id=patient_id,
                recommendation_type="screening",
                title="Colorectal Cancer Screening",
                description="Consider colonoscopy for colorectal cancer screening",
                rationale="USPSTF Grade A recommendation for adults 50-75",
                confidence=RecommendationConfidence.HIGH,
                evidence_sources=["USPSTF Guidelines"],
                action_required=False,
                priority=3,
                created_at=datetime.utcnow()
            ))
        
        return recommendations
    
    def _generate_monitoring_recommendations(self, medications: List[str]) -> List[ClinicalRecommendation]:
        """Generate medication monitoring recommendations"""
        
        recommendations = []
        
        for med_name in medications:
            drug = self.drug_database.search_drug(med_name)
            if drug and drug.monitoring_requirements:
                for monitoring in drug.monitoring_requirements:
                    recommendations.append(ClinicalRecommendation(
                        id=str(uuid.uuid4()),
                        patient_id="",  # Will be set by caller
                        recommendation_type="monitoring",
                        title=f"Monitor {monitoring} for {drug.name}",
                        description=f"Regular monitoring of {monitoring} required",
                        rationale=f"Drug safety monitoring for {drug.name}",
                        confidence=RecommendationConfidence.HIGH,
                        evidence_sources=["Drug prescribing information"],
                        action_required=True,
                        priority=2,
                        created_at=datetime.utcnow()
                    ))
        
        return recommendations
    
    def _review_medications(self, medications: List[str], patient: Client) -> Dict[str, Any]:
        """Review patient medications for appropriateness"""
        
        issues = []
        recommendations = []
        
        age = None
        if patient.dob:
            age = (datetime.utcnow().date() - patient.dob).days // 365
        
        for med_name in medications:
            drug = self.drug_database.search_drug(med_name)
            if not drug:
                continue
            
            # Age-related considerations
            if age and age >= 65:
                # Beers Criteria considerations (simplified)
                high_risk_classes = ["benzodiazepines", "anticholinergics", "tricyclic antidepressants"]
                for drug_class in drug.drug_class:
                    if drug_class.lower() in high_risk_classes:
                        issues.append(f"{drug.name} may be inappropriate for elderly patients")
        
        return {
            "issues_identified": issues,
            "optimization_recommendations": recommendations,
            "review_date": datetime.utcnow().isoformat()
        }
    
    def _assess_patient_risk(self, patient: Client, recent_visits: List[Visit]) -> Dict[str, Any]:
        """Assess patient risk factors"""
        
        risk_factors = []
        risk_score = 0
        
        # Age-based risk
        if patient.dob:
            age = (datetime.utcnow().date() - patient.dob).days // 365
            if age >= 65:
                risk_factors.append("Advanced age")
                risk_score += 1
        
        # Frequent visits indicator
        if len(recent_visits) > 6:  # More than 6 visits in 90 days
            risk_factors.append("Frequent healthcare utilization")
            risk_score += 2
        
        # Multiple diagnoses
        diagnoses = set()
        for visit in recent_visits:
            if visit.diagnosis:
                diagnoses.add(visit.diagnosis)
        
        if len(diagnoses) > 3:
            risk_factors.append("Multiple comorbidities")
            risk_score += 2
        
        risk_level = "high" if risk_score >= 4 else "moderate" if risk_score >= 2 else "low"
        
        return {
            "risk_level": risk_level,
            "risk_score": risk_score,
            "risk_factors": risk_factors,
            "recommendations": self._get_risk_based_recommendations(risk_level)
        }
    
    def _get_risk_based_recommendations(self, risk_level: str) -> List[str]:
        """Get recommendations based on risk level"""
        
        if risk_level == "high":
            return [
                "Consider care coordination",
                "Frequent monitoring recommended",
                "Medication reconciliation",
                "Consider advance directives"
            ]
        elif risk_level == "moderate":
            return [
                "Regular follow-up appointments",
                "Medication review",
                "Preventive care screening"
            ]
        else:
            return [
                "Routine preventive care",
                "Annual wellness visit"
            ]

# Global instance
clinical_decision_engine = ClinicalDecisionEngine()
