from north_admin import AuthProvider, UserReturnSchema, NorthAdmin, AdminRouter, FilterGroup, Filter
from north_admin.types import AdminMethods, FieldType
from sqlalchemy import select, and_, bindparam
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.database.models import User, Subscription, Company, Category, FinancialStatement


class AdminAuthProvider(AuthProvider):
    async def login(
            self,
            session: AsyncSession,
            login: str,
            password: str,
    ) -> User | None:
        query = (
            select(User)
            .filter(User.email == login)
            .filter(User.superuser == True)
        )

        return await session.scalar(query)

    async def get_user_by_id(
            self,
            session: AsyncSession,
            user_id: str,
    ) -> User | None:
        query = (
            select(User)
            .filter(User.id == user_id)
            .filter(User.superuser == True)
        )

        return await session.scalar(query)

    async def to_user_scheme(
            self,
            user: User,
    ) -> UserReturnSchema:
        return UserReturnSchema(
            id=user.id,
            login=user.email,
            fullname="smth",
        )


admin_app = NorthAdmin(
    sqlalchemy_uri=settings.postgres_url,
    jwt_secket_key='JNBjdejjn!w443@wer',
    auth_provider=AdminAuthProvider,
)

user_get_columns = [
    User.id,
    User.email,
    User.superuser,
]

subscription_get_columns = [
    Subscription.id,
    Subscription.transaction_id,
    Subscription.type,
    Subscription.status,
    Subscription.created_at,
    Subscription.expired_at,
]

company_get_columns = [
    Company.cik,
    Company.name,
    Company.ticker,
    Company.sic,
    Company.business_address,
    Company.mailing_address,
    Company.phone,
]

category_get_columns = [
    Category.tag,
    Category.category,
    Category.label,
]

financial_statement_get_columns = [
    FinancialStatement.accession_number,
    FinancialStatement.period,
    FinancialStatement.filing_date,
    FinancialStatement.report_date,
    FinancialStatement.form,
    FinancialStatement.value,
    FinancialStatement.cik,
    FinancialStatement.tag,
]

admin_app.add_admin_routes(
    AdminRouter(
        model=User,
        model_title='Users',
        enabled_methods=[
            AdminMethods.CREATE,
            AdminMethods.UPDATE,
            AdminMethods.GET_ONE,
            AdminMethods.GET_LIST,
        ],
        pkey_column=User.id,
        get_columns=user_get_columns,
        list_columns=user_get_columns,
        filters=[
            FilterGroup(
                query=(
                    and_(
                        User.id > bindparam('id_greater_than_param'),
                    )
                ),
                filters=[
                    Filter(
                        bindparam='id_greater_than_param',
                        title='ID greater than',
                        field_type=FieldType.STRING,
                    ),
                ],
            ),
            FilterGroup(
                query=(User.id == bindparam('exact_id_param')),
                filters=[
                    Filter(
                        bindparam='exact_id_param',
                        title='Exact ID',
                        field_type=FieldType.STRING,
                    )
                ],
            ),
        ]
    )
)

admin_app.add_admin_routes(
    AdminRouter(
        model=Subscription,
        model_title='Subscriptions',
        enabled_methods=[
            AdminMethods.CREATE,
            AdminMethods.UPDATE,
            AdminMethods.GET_ONE,
            AdminMethods.GET_LIST,
        ],
        pkey_column=Subscription.id,
        soft_delete_column=None,
        get_columns=subscription_get_columns,
        list_columns=subscription_get_columns,
        filters=[
            FilterGroup(
                query=(
                    and_(
                        Subscription.id > bindparam('id_greater_than_param'),
                    )
                ),
                filters=[
                    Filter(
                        bindparam='id_greater_than_param',
                        title='ID greater than',
                        field_type=FieldType.STRING,
                    ),
                ],
            ),
            FilterGroup(
                query=(Subscription.id == bindparam('exact_id_param')),
                filters=[
                    Filter(
                        bindparam='exact_id_param',
                        title='Exact ID',
                        field_type=FieldType.STRING,
                    )
                ],
            ),
        ]
    )
)

admin_app.add_admin_routes(
    AdminRouter(
        model=Company,
        model_title='Companies',
        enabled_methods=[
            AdminMethods.CREATE,
            AdminMethods.UPDATE,
            AdminMethods.GET_ONE,
            AdminMethods.GET_LIST,
        ],
        pkey_column=Company.cik,
        soft_delete_column=None,
        get_columns=company_get_columns,
        list_columns=company_get_columns,
        filters=[
            FilterGroup(
                query=(
                    and_(
                        Company.cik > bindparam('id_greater_than_param'),
                    )
                ),
                filters=[
                    Filter(
                        bindparam='id_greater_than_param',
                        title='ID greater than',
                        field_type=FieldType.STRING,
                    ),
                ],
            ),
            FilterGroup(
                query=(Company.cik == bindparam('exact_id_param')),
                filters=[
                    Filter(
                        bindparam='exact_id_param',
                        title='Exact ID',
                        field_type=FieldType.STRING,
                    )
                ],
            ),
        ]
    )
)

admin_app.add_admin_routes(
    AdminRouter(
        model=Category,
        model_title='Categories',
        enabled_methods=[
            AdminMethods.CREATE,
            AdminMethods.UPDATE,
            AdminMethods.GET_ONE,
            AdminMethods.GET_LIST,
        ],
        pkey_column=Category.tag,
        soft_delete_column=None,
        get_columns=category_get_columns,
        list_columns=category_get_columns,
        filters=[
            FilterGroup(
                query=(
                    and_(
                        Category.tag > bindparam('id_greater_than_param'),
                    )
                ),
                filters=[
                    Filter(
                        bindparam='id_greater_than_param',
                        title='ID greater than',
                        field_type=FieldType.STRING,
                    ),
                ],
            ),
            FilterGroup(
                query=(Category.tag == bindparam('exact_id_param')),
                filters=[
                    Filter(
                        bindparam='exact_id_param',
                        title='Exact ID',
                        field_type=FieldType.STRING,
                    )
                ],
            ),
        ]
    )
)

admin_app.add_admin_routes(
    AdminRouter(
        model=FinancialStatement,
        model_title='FinancialStatements',
        enabled_methods=[
            AdminMethods.CREATE,
            AdminMethods.UPDATE,
            AdminMethods.GET_ONE,
            AdminMethods.GET_LIST,
        ],
        pkey_column=FinancialStatement.accession_number,
        soft_delete_column=None,
        get_columns=financial_statement_get_columns,
        list_columns=financial_statement_get_columns,
        filters=[
            FilterGroup(
                query=(
                    and_(
                        FinancialStatement.accession_number > bindparam('id_greater_than_param'),
                    )
                ),
                filters=[
                    Filter(
                        bindparam='id_greater_than_param',
                        title='ID greater than',
                        field_type=FieldType.STRING,
                    ),
                ],
            ),
            FilterGroup(
                query=(FinancialStatement.accession_number == bindparam('exact_id_param')),
                filters=[
                    Filter(
                        bindparam='exact_id_param',
                        title='Exact ID',
                        field_type=FieldType.STRING,
                    )
                ],
            ),
        ]
    )
)