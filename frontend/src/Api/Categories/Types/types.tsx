export enum CategoryType {
    API_TAG = "api_tag",
    CUSTOM_FORMULA = "custom_formula",
    EXACT_VALUE = "exact_value"
}

export enum SortByType {
    ASC = "asc",
    DESC = "desc",
}


export interface ICategory {
    value_definition: string;
    label: string;
    description: string,
    id: string,
    priority: number,
    type: string,
}


export interface IPaginationData {
    current_page: number;
    total_page: number;
    total_results: number;
}

export interface IGetAllCategoriesResponse {
    status: number;
    detail: string;
    result: {
        categories: ICategory[];
        pagination: IPaginationData
    }
}

export interface ICreateCategory {
    label: string,
    value_definition: string,
    description: string,
    type: CategoryType,
    priority: number
}
export interface ICategoryUpdate {
    label: string,
    value_definition: string,
    description: string,
    type: CategoryType,
    priority: number
}


export interface DeleteResponse {
    detail: string;
    status: number;
}
