import uuid
from django.db import models
from apps.core.models import Organization, User

class OnboardingTemplate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='onboarding_templates')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    supplier_category = models.CharField(max_length=100)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.supplier_category})"

class DocumentType(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='document_types')
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50)
    description = models.TextField(blank=True, null=True)
    is_required = models.BooleanField(default=True)
    default_expiry_days = models.IntegerField(default=365)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('organization', 'code')

    def __str__(self):
        return self.name

class DocumentRequirement(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    template = models.ForeignKey(OnboardingTemplate, on_delete=models.CASCADE, related_name='requirements')
    document_type = models.ForeignKey(DocumentType, on_delete=models.CASCADE)
    is_mandatory = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.template.name} - {self.document_type.name}"

class Supplier(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        INVITED = 'INVITED', 'Invited'
        IN_REVIEW = 'IN_REVIEW', 'In Review'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'
        SUSPENDED = 'SUSPENDED', 'Suspended'

    class RiskLevel(models.TextChoices):
        LOW = 'LOW', 'Low Risk'
        MEDIUM = 'MEDIUM', 'Medium Risk'
        HIGH = 'HIGH', 'High Risk'
        CRITICAL = 'CRITICAL', 'Critical Risk'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='suppliers')
    template = models.ForeignKey(OnboardingTemplate, on_delete=models.SET_NULL, null=True, blank=True, related_name='suppliers')
    
    legal_name = models.CharField(max_length=255)
    trading_name = models.CharField(max_length=255, blank=True, null=True)
    supplier_code = models.CharField(max_length=50, blank=True, null=True)
    category = models.CharField(max_length=100, default='Manufacturing')
    country = models.CharField(max_length=100, default='India')
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.PENDING)
    
    website = models.URLField(blank=True, null=True)
    company_email = models.EmailField()
    phone = models.CharField(max_length=50, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=50, blank=True, null=True)
    
    invitation_token = models.CharField(max_length=100, unique=True, default=uuid.uuid4)
    invitation_sent_at = models.DateTimeField(null=True, blank=True)
    onboarding_completed_at = models.DateTimeField(null=True, blank=True)
    onboarding_deadline = models.DateField(null=True, blank=True)
    
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_suppliers')
    
    compliance_score = models.IntegerField(default=100)
    risk_level = models.CharField(max_length=20, choices=RiskLevel.choices, default=RiskLevel.LOW)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return self.legal_name

class SupplierContact(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='contacts')
    name = models.CharField(max_length=255)
    title = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField()
    phone = models.CharField(max_length=50, blank=True, null=True)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.supplier.legal_name})"

class SupplierBankDetails(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    supplier = models.OneToOneField(Supplier, on_delete=models.CASCADE, related_name='bank_details')
    bank_name = models.CharField(max_length=255, blank=True, null=True)
    account_name = models.CharField(max_length=255, blank=True, null=True)
    account_number = models.CharField(max_length=100, blank=True, null=True)
    routing_number = models.CharField(max_length=100, blank=True, null=True)
    swift_bic = models.CharField(max_length=50, blank=True, null=True)
    iban = models.CharField(max_length=50, blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.bank_name} - {self.supplier.legal_name}"

class SupplierTaxInformation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    supplier = models.OneToOneField(Supplier, on_delete=models.CASCADE, related_name='tax_info')
    tax_id_number = models.CharField(max_length=100, blank=True, null=True)
    gst_vat_number = models.CharField(max_length=100, blank=True, null=True)
    tax_residency_country = models.CharField(max_length=100, default='India')
    is_exempt = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Tax Info: {self.supplier.legal_name}"
