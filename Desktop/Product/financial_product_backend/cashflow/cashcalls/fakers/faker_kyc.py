from xml.dom.minidom import DocumentType

import factory
from django.forms import DateField
from factory.fuzzy import FuzzyChoice

from core_management.factories.factory_kyc import KYCFactory
from core_management.factories.factory_kyc import MangoPayRelationFactory
from core_management.fakers.faker_address import AddressFaker
from core_management.fakers.faker_address import CountryFaker
from core_management.models import Country
from core_management.models import MangoPayRelation
from core_management.models import mangopay_integrated_entities
from entities.investor.choices import KYCDocumentStatusChoices
from entities.investor.choices import KYCStatusChoices
from legal.general.choices.choices_kyc import KYCTypeChoices
from legal.kyc_fund.fakers.faker_kyc_fund import KYCFundFaker
from ort import choices
from ort_files.document.fakers import FakeDocumentFactory


class MangoPayRelationFaker(MangoPayRelationFactory):
    entity = FuzzyChoice([choice[1] for choice in mangopay_integrated_entities])


class KYCFaker(KYCFactory):
    mangopay_relation: MangoPayRelation = factory.SubFactory(MangoPayRelationFaker)
    representant_nationality: Country = factory.SubFactory(CountryFaker)
    country_of_residence: Country = factory.SubFactory(CountryFaker)
    type: str = KYCTypeChoices.natural.name
    status: str = FuzzyChoice([choice[1] for choice in KYCStatusChoices.choices()])
    email: str = factory.Faker("email")
    first_name: str = factory.Faker("first_name")
    last_name: str = factory.Faker("last_name")
    business_address: str = factory.SubFactory(AddressFaker)
    representative_address: str = factory.SubFactory(AddressFaker)
    birthday: DateField = factory.Faker("date")
    company_name: str = factory.Faker("company")
    status_proof_of_residency: str = KYCDocumentStatusChoices.get_value("pending")
    bank_details: str = factory.Faker("iban")


class KYCWithDocumentsFaker(KYCFaker):
    document_identity_of_proof: DocumentType = factory.SubFactory(FakeDocumentFactory)
    document_articles_of_association: DocumentType = factory.SubFactory(
        FakeDocumentFactory
    )
    document_registration_proof: DocumentType = factory.SubFactory(FakeDocumentFactory)
    document_shareholder_declaration: DocumentType = factory.SubFactory(
        FakeDocumentFactory
    )
    document_proof_of_residency: DocumentType = factory.SubFactory(FakeDocumentFactory)


class KYCFundDocumentsFaker(KYCFundFaker):
    kbis_extract_document: DocumentType = factory.SubFactory(FakeDocumentFactory)
    articles_of_incorporation_document: DocumentType = factory.SubFactory(
        FakeDocumentFactory
    )
    official_register_extract_document: DocumentType = factory.SubFactory(
        FakeDocumentFactory
    )
    investor_company_accreditation_document: DocumentType = factory.SubFactory(
        FakeDocumentFactory
    )
    form_of_authority: DocumentType = factory.SubFactory(FakeDocumentFactory)
