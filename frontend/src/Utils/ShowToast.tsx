import toast from "react-hot-toast";
import {Toast} from "../Components/Toast/ui/Toast";

export const showToast = (type: 'success' | 'error', title: string, text: string) => {
    toast(({ id }) => (
        <Toast id={id} type={type} title={title} text={text} />
    ));
};