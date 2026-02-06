import logging
from sqlalchemy.orm import Session

from ..models import Template, TemplateField
from ..exceptions import NotFoundError

logger = logging.getLogger(__name__)


class TemplateService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_all(self) -> list[Template]:
        return self.db.query(Template).order_by(Template.created_at.desc()).all()
    
    def get_by_id(self, template_id: int) -> Template:
        template = self.db.query(Template).filter(Template.id == template_id).first()
        if not template:
            raise NotFoundError("Template", template_id)
        return template
    
    def create(self, name: str, document_type: str, description: str | None = None) -> Template:
        template = Template(name=name, description=description, document_type=document_type)
        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        return template
    
    def update(self, template_id: int, **kwargs) -> Template:
        template = self.get_by_id(template_id)
        for key, value in kwargs.items():
            if value is not None and hasattr(template, key):
                setattr(template, key, value)
        self.db.commit()
        self.db.refresh(template)
        return template
    
    def delete(self, template_id: int) -> None:
        template = self.get_by_id(template_id)
        self.db.delete(template)
        self.db.commit()
    
    def add_field(
        self,
        template_id: int,
        field_name: str,
        field_label: str,
        field_type: str,
        description: str | None = None,
        normalization_rule: str | None = None,
        is_required: bool = False,
        validation_rules: dict | None = None
    ) -> TemplateField:
        self.get_by_id(template_id)
        max_order = self.db.query(TemplateField).filter(
            TemplateField.template_id == template_id
        ).count()
        
        # Increment template version when fields change
        template = self.get_by_id(template_id)
        template.version = (template.version or 1) + 1
        
        field = TemplateField(
            template_id=template_id,
            field_name=field_name,
            field_label=field_label,
            field_type=field_type,
            description=description,
            normalization_rule=normalization_rule,
            is_required=is_required,
            order_index=max_order,
            validation_rules=validation_rules
        )
        self.db.add(field)
        self.db.commit()
        self.db.refresh(field)
        return field
    
    def update_field(self, field_id: int, **kwargs) -> TemplateField:
        field = self.db.query(TemplateField).filter(TemplateField.id == field_id).first()
        if not field:
            raise NotFoundError("TemplateField", field_id)
        
        for key, value in kwargs.items():
            if value is not None and hasattr(field, key):
                setattr(field, key, value)
        
        self.db.commit()
        self.db.refresh(field)
        return field
    
    def delete_field(self, field_id: int) -> None:
        field = self.db.query(TemplateField).filter(TemplateField.id == field_id).first()
        if not field:
            raise NotFoundError("TemplateField", field_id)
        self.db.delete(field)
        self.db.commit()
    
    def reorder_fields(self, template_id: int, field_ids: list[int]) -> None:
        self.get_by_id(template_id)
        for index, field_id in enumerate(field_ids):
            field = self.db.query(TemplateField).filter(
                TemplateField.id == field_id,
                TemplateField.template_id == template_id
            ).first()
            if field:
                field.order_index = index
        self.db.commit()
    
    def create_default_templates(self) -> None:
        if self.db.query(Template).count() > 0:
            return
        
        self._create_nda_template()
        self._create_contract_template()
        self._create_lease_template()
        self.db.commit()
        logger.info("Default templates created successfully")
    
    def _create_nda_template(self) -> None:
        template = self.create("NDA Template", "nda", "Standard Non-Disclosure Agreement fields")
        fields = [
            ("disclosing_party", "Disclosing Party", "party", "The party sharing confidential information", "uppercase", True),
            ("receiving_party", "Receiving Party", "party", "The party receiving confidential information", "uppercase", True),
            ("effective_date", "Effective Date", "date", "Date when the agreement becomes effective", "iso_date", True),
            ("term_duration", "Term/Duration", "text", "How long the agreement lasts", None, True),
            ("confidential_info_definition", "Confidential Information Definition", "clause", "Definition of what constitutes confidential information", None, True),
            ("exclusions", "Exclusions", "clause", "What is excluded from confidential information", None, False),
            ("permitted_use", "Permitted Use", "clause", "How the receiving party may use the information", None, False),
            ("governing_law", "Governing Law", "text", "Which jurisdiction's laws govern the agreement", None, False),
        ]
        for name, label, ftype, desc, norm, req in fields:
            self.add_field(template.id, name, label, ftype, desc, norm, req)
    
    def _create_contract_template(self) -> None:
        template = self.create("Service Agreement Template", "contract", "Standard service agreement fields")
        fields = [
            ("party_a", "Party A (Provider)", "party", "The service provider", "uppercase", True),
            ("party_b", "Party B (Client)", "party", "The client receiving services", "uppercase", True),
            ("effective_date", "Effective Date", "date", "Contract start date", "iso_date", True),
            ("termination_date", "Termination Date", "date", "Contract end date", "iso_date", False),
            ("contract_value", "Contract Value", "currency", "Total contract amount", "currency_usd", True),
            ("payment_terms", "Payment Terms", "text", "Payment schedule and terms", None, True),
            ("scope_of_services", "Scope of Services", "clause", "Description of services to be provided", None, True),
            ("termination_clause", "Termination Clause", "clause", "Conditions for terminating the agreement", None, False),
            ("liability_cap", "Liability Cap", "currency", "Maximum liability amount", "currency_usd", False),
            ("governing_law", "Governing Law", "text", "Applicable jurisdiction", None, False),
        ]
        for name, label, ftype, desc, norm, req in fields:
            self.add_field(template.id, name, label, ftype, desc, norm, req)
    
    def _create_lease_template(self) -> None:
        template = self.create("Commercial Lease Template", "lease", "Commercial property lease fields")
        fields = [
            ("landlord", "Landlord", "party", "Property owner", "uppercase", True),
            ("tenant", "Tenant", "party", "Property renter", "uppercase", True),
            ("property_address", "Property Address", "text", "Address of leased property", None, True),
            ("lease_start_date", "Lease Start Date", "date", "When the lease begins", "iso_date", True),
            ("lease_end_date", "Lease End Date", "date", "When the lease ends", "iso_date", True),
            ("monthly_rent", "Monthly Rent", "currency", "Monthly rental amount", "currency_usd", True),
            ("security_deposit", "Security Deposit", "currency", "Required security deposit", "currency_usd", True),
            ("renewal_terms", "Renewal Terms", "clause", "Options for lease renewal", None, False),
            ("maintenance_responsibilities", "Maintenance Responsibilities", "clause", "Who is responsible for maintenance", None, False),
            ("permitted_use", "Permitted Use", "clause", "Allowed uses of the property", None, False),
        ]
        for name, label, ftype, desc, norm, req in fields:
            self.add_field(template.id, name, label, ftype, desc, norm, req)
