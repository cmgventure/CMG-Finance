import apiHandler from "../ApiHandler";
import {
    DeleteResponse,
    ICategoryUpdate,
    ICreateCategory,
    IGetAllCategoriesResponse,
} from "./Types/types";
import ApiHandler from "../ApiHandler";

export const getAllCategories = async (page: number, page_size: number) => {
    try {
        const response = await apiHandler.get<IGetAllCategoriesResponse>("/admin/categories", {
            params: {
                page,
                page_size,
            },
        });
        return response.data

    } catch (error) {
        console.error('Error:', error);
        throw error;
    }
};

export const createCategory = async (data: ICreateCategory) => {
    try {
        const response = await ApiHandler.post<ICreateCategory>(`/admin/categories`, data);
        if ([200, 201].includes(response.status)) {
            return {
                status: response.status,
                result: 'success',
                data: response.data
            };
        }
    } catch {
        return {
            status: 500,
            result: 'failed'
        };
    }
}

export const deleteCategory= async (category_id: string) => {
    try {
        const response = await ApiHandler.delete<DeleteResponse>(`/admin/categories/${category_id}/`)
        if (response.status === 200) {
            return response.status;
        } else {
            return 500;
        }
    } catch(error) {
        return 500
    }
}

export const updateCategory = async (category_id: string, data: ICategoryUpdate) => {
    try {
        const response = await apiHandler.patch(`/admin/categories/${category_id}`, data);
        if (response.status === 200) {
            return { success: true, message: 'Category updated successfully' , category: response.data};
        } else {
            return { success: false, message: 'Category updating failed', category: null };
        }
    } catch (error) {
        return { success: false, message: 'Category updating failed' , category: null};
    }
};
