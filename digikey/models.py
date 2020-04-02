"""
Types that wrap responses from the Octopart API
and make various attributes easier to access.
"""

import inflection

from schematics.exceptions import ConversionError, DataError, ValidationError
from schematics.models import Model
from schematics.types import BooleanType, IntType, StringType
from schematics.types.compound import ListType, ModelType

from enum import Enum


class BaseModel(Model):
    @classmethod
    def errors(cls, dict_):
        """
        Wraps `schematics` validate method to return an error list instead of
        having to catch an exception in the caller.
        Returns:
            list of validation errors, or None.
        """
        try:
            cls(dict_).validate()
            return None
        except (DataError, ValidationError) as err:
            return err.messages

    @classmethod
    def errors_list(cls, list_):
        """
        Return any validation errors in list of dicts.
        Args:
            list_ (list): dicts to be validated.
        Returns:
            list of errors, if any, otherwise None.
        """
        try:
            errors = [cls(dict_).errors for dict_ in list_]
            if any(errors):
                return [_f for _f in errors if _f]
            return None
        except (ConversionError, DataError) as err:
            return err.messages

    @classmethod
    def is_valid(cls, dict_):
        return not cls.errors(dict_)

    @classmethod
    def is_valid_list(cls, list_):
        try:
            return all([cls(dict_).is_valid for dict_ in list_])
        except (ConversionError, DataError):
            return False

    @classmethod
    def camelize(cls, dict_):
        return cls.recursive_camelize(dict_)

    @staticmethod
    def recursive_camelize(camelizee):
        # Camelizes objects and their children, also supports lists of objects
        if isinstance(camelizee, dict):
            # If the camelizee is a dictionary camelize its keys and call recursive_camelize on its values
            return {inflection.camelize(k): BaseModel.recursive_camelize(v) for k, v in camelizee.items()}
        elif isinstance(camelizee, list):
            # If the camelizee is a list call recursive_camelize on each element
            return [BaseModel.recursive_camelize(d) for d in camelizee]
        else:
            # Otherwise return the value
            return camelizee

    @classmethod
    def underscore(cls, underscoree):
        return cls.recursive_underscore(underscoree)

    @staticmethod
    def recursive_underscore(underscoree):
        # Same as recursive_camelize except goes to underscore
        if isinstance(underscoree, dict):
            return {inflection.underscore(k): BaseModel.recursive_underscore(v) for k, v in underscoree.items()}
        elif isinstance(underscoree, list):
            return [BaseModel.recursive_underscore(d) for d in underscoree]
        else:
            return underscoree


class ParametricFilters(BaseModel):
    # Parameter ID to filter on
    parameter_id = IntType(required=True)
    # Value ID to filter by
    value_id = StringType(required=True, min_length=1, max_length=100)


class Filters(BaseModel):
    # Taxonomy IDs to filter by
    taxonomy_ids = ListType(IntType)
    # Manufacturer IDs to filter by
    manufacturer_ids = ListType(IntType)
    # Parametric Filters to filter by
    parametric_filters = ListType(ModelType(ParametricFilters))


class SortOptions(Enum):
    # Enum storing the possible values for the sort option
    sort_by_digi_key_part_number = 'SortByDigiKeyPartNumber'
    sort_by_manufacturer_part_number = 'SortByManufacturerPartNumber'
    sort_by_description = 'SortByDescription'
    sort_by_manufacturer = 'SortByManufacturer'
    sort_by_minimum_order_quantity = 'SortByMinimumOrderQuantity'
    sort_by_quantity_available = 'SortByQuantityAvailable'
    sort_by_unit_price = 'SortByUnitPrice'
    sort_by_parameter = 'SortByParameter'


class SortDirections(Enum):
    # Enum storing the possible values for the sort direction
    ascending = 'Ascending'
    descending = 'Descending'


class Sort(BaseModel):
    # Class to store the sort parameters

    # Sets the value to sort by
    sort_option = StringType(required=True, choices=[c.value for c in SortOptions])
    # Sets the sort direction
    direction = StringType(required=True, choices=[c.value for c in SortDirections])
    # If sorting by parameter, sets the parameter to sort by
    sort_parameter_id = IntType()

    # Make sure that a sort parameter id is provided if sorting by parameter.
    def validate_sort_parameter_id(self, data, value):
        if data['sort_option'] == SortOptions.sort_by_parameter.value:
            if data['sort_parameter_id'] is None:
                raise ValidationError('If sorting by parameter a sort parameter must be set')
        else:
            if data['sort_parameter_id'] is not None:
                raise ValidationError('If not sorting by parameter no sort parameter id should be provided')

        return value


class SearchOptions(Enum):
    #  Enum storing possible search_options
    lead_free = 'LeadFree'
    collapse_packaging_types = 'CollapsePackagingTypes'
    exclude_non_stock = 'ExcludeNonStock'
    has_3d_model = 'Has3DModel'
    in_stock = 'InStock'
    manufacturer_part_search = 'ManufacturerPartSearch'
    new_products_only = 'NewProductsOnly'
    rohs_compliant = 'RoHSCompliant'
    has_mentor_footprint = 'HasMentorFootprint'


class KeywordSearchRequest(BaseModel):
    """Query format sent to the search endpoint
    https://api-portal.digikey.com/node/8517
    """
    # Keywords to search on
    keywords = StringType(required=True)
    # Filters the search results by the included SearchOptions
    search_options = ListType(StringType(choices=[c.value for c in SearchOptions]))
    # Maximum number of items to return
    record_count = IntType(default=10, min_value=1, max_value=50, required=True)
    # Ordinal position of first returned item
    record_start_pos = IntType(default=0)
    # Set Filters to narrow down search response
    filters = ModelType(Filters)
    # Sort Parameters
    sort = ModelType(Sort)
    # The RequestedQuantity is used with the SortByUnitPrice Sort Option to sort by unit price at the RequestedQuantity
    requested_quantity = IntType(default=1)


class PartDetailPostRequest(BaseModel):
    """Query format sent to the partdetails endpoint
    https://api-portal.digikey.com/node/8517
    """
    # Part number. Works best with Digi-Key part numbers.
    part = StringType(required=True)
    # The option to include all Associated products
    include_all_associated_products = BooleanType()
    # The option to include all For Use With products
    include_all_for_use_with_products = BooleanType()

class ProductDetailGetRequest(BaseModel):
    """Query format sent to the partdetails endpoint
    https://api-portal.digikey.com/node/8517
    """
    # Part number. Works best with Digi-Key part numbers.
    part = StringType(required=True)
    includes = StringType(required=False)
#TODO: How to best keep these fields include_all_associated_products, include_all_for_use_with_products from PartDetailPostRequest


class KeywordSearchResult:
    def __init__(self, result):
        self._result = result

        # Get limited taxonomy information
        self.limited_taxonomy = LimitedTaxonomy(BaseModel.underscore(result['LimitedTaxonomy']))

        # Get filter option information
        self.filter_options = [FilterOption(BaseModel.underscore(filter_option))
                               for filter_option in result['FilterOptions']]

    @property
    def products(self):
        return [
            Part(result)
            for result in self._result.get('Products', [])
        ]

    def __repr__(self):
        return '<KeywordSearchResult: hits=%s>' % self._result['ProductsCount']

    def pretty_print(self):
        print(self)
        for product in self.products:
            print('\t%s' % product)


''' 
Helper classes for responses
'''


class LimitedTaxonomy(BaseModel):
    # The number of products in this taxon
    product_count = IntType()
    # The number of new products in this taxon
    new_product_count = IntType()
    # The parameter id of taxonomy (Should always be the same for all taxa.)
    parameter_id = IntType()
    # The value id for this taxon.
    value_id = StringType()
    # The parameter of taxonomy (Should always be the same for all taxa.)
    parameter = StringType()
    # The name of this taxon.
    value = StringType()

    # Value is the most interesting property of a Taxon
    def __repr__(self):
        return self.value


# Some taxa have child taxa that are themselves LimitedTaxonomy objects (with child taxa of their own)
# We must add this outside of the class definition as it is self referential.
# noinspection PyProtectedMember,PyTypeChecker
LimitedTaxonomy._append_field('children', ListType(ModelType(LimitedTaxonomy)))


class Value(BaseModel):
    # Value of a Filter Option

    # The value id
    value_id = StringType()
    # The value itself (e.g. number with units)
    value = StringType()

    # Value id and value are generally both of interest
    def __repr__(self):
        return '{{{:} : {:}}}'.format(self.value_id, self.value)


class FilterOption(BaseModel):
    # Class for storing a searches filter options

    # A list of possible values for the parameter
    values = ListType(ModelType(Value))

    # The id of the filter parameter
    parameter_id = IntType()
    # The name of the filter parameter
    parameter = StringType()

    # Parameter id and name are generally both of interest
    def __repr__(self):
        return '{{{:} : {:}}}'.format(self.parameter_id, self.parameter)


class PriceBreak:
    def __init__(self, pricebreak: dict):
        self._pricebreak = pricebreak

    @property
    def breakquantity(self) -> int:
        return self._pricebreak.get('BreakQuantity', 0)

    @property
    def unitprice(self) -> float:
        return self._pricebreak.get('UnitPrice', 0.0)

    @property
    def totalprice(self) -> float:
        return self._pricebreak.get('TotalPrice', 0.0)


class IdTextPair:
    def __init__(self, idtextpair: dict):
        self._idtextpair = idtextpair

    @property
    def id(self) -> str:
        return self._idtextpair.get('Id', '')

    @property
    def text(self) -> str:
        return self._idtextpair.get('Text', '')


class PidVid:
    def __init__(self, pidvid: dict):
        self._pidvid = pidvid

    @property
    def parameter_id(self) -> int:
        return self._pidvid.get('ParameterId', 0)

    @property
    def value_id(self) -> int:
        return self._pidvid.get('ValueId', 0)

    @property
    def parameter(self) -> str:
        return self._pidvid.get('Parameter', '')

    @property
    def value(self) -> str:
        return self._pidvid.get('Value', '')

    def __repr__(self):
        return '<PidVid param={} val={}>'.format(self.parameter, self.value)


class Family:
    def __init__(self, family: dict):
        self._family = family

    @property
    def id(self) -> str:
        return self._family.get('Id', '')

    @property
    def name(self) -> str:
        return self._family.get('Name', '')

    @property
    def part_count(self) -> int:
        return self._family.get('PartCount', 0)


class Part:
    def __init__(self, part: dict):
        self._part = part

    @property
    def standard_pricing(self) -> list:
        return [
            PriceBreak(part)
            for part in self._part.get('StandardPricing', [])
        ]

    @property
    def category(self) -> IdTextPair:
        return IdTextPair(self._part.get('Category', {}))

    @property
    def family(self) -> IdTextPair:
        return IdTextPair(self._part.get('Family', {}))

    @property
    def manufacturer(self) -> str:
        return PidVid(self._part.get('Manufacturer', {})).value

    @property
    def mpn(self) -> str:
        return self._part.get('ManufacturerPartNumber', None)

    @property
    def part_status(self) -> str:
        return self._part.get('PartStatus', None)

    @property
    def digikey_pn(self) -> str:
        return self._part.get('DigiKeyPartNumber', None)

    @property
    def digikey_url(self) -> str:
        return 'https://www.digikey.com' + self._part.get('PartUrl', '')

    @property
    def in_stock(self) -> int:
        return self._part.get('QuantityAvailable', None)

    @property
    def moq(self) -> int:
        return self._part.get('MinimumOrderQuantity', None)

    @property
    def parameters(self) -> dict:
        _params = [PidVid(param) for param in self._part.get('Parameters', [])]
        return {p.parameter: p.value for p in _params}

    @property
    def description_product(self) -> str:
        return self._part.get('ProductDescription', None)

    @property
    def description_detailed(self) -> str:
        return self._part.get('DetailedDescription', None)

    @property
    def datasheet(self) -> str:
        return self._part.get('PrimaryDatasheet', None)

    def __repr__(self):
        return '<Part mpn=%s>' % self.mpn
