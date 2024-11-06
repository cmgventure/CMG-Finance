import { FC } from 'react';
import styles from './Toast.module.scss';
import toast from 'react-hot-toast';
import {Button} from "~/Components/Button";
import WarningIcon from "~/Icons/WarningIcon/WarningIcon.tsx";
import StarIcon from "~/Icons/StarIcon/StarIcon.tsx";


interface IToastProps {
  title: string;
  type: 'success' | 'error' | 'warning';
  text?: string;
  id?: string;
  className?: string;
}

/**
 * @param props - The props for the component.
 * @param title - the toast title.
 * @param type - The toast type 'success' | 'error' | 'warning'.
 * @param text - The toast text.
 * @param id - ID for the toast.
 * @description - Toast shared component
 * @returns A React component that displays an toast.
 */

const Toast: FC<IToastProps> = (props) => {
  const { title, text, type, id, className } = props;

  return (
    <div className={[styles.toast, className, styles[type]].join(' ')}>
      <div className={styles.img}>
          {type === 'success' ? <StarIcon width={'20'} height={'20'} stroke={'green'}/> : <WarningIcon/>}
      </div>
      <div className={styles.wrap}>
        <p className={styles.title}>{title}</p>
        <p className={styles.text}>{text}</p>
      </div>
      {id && (
        <Button
          variant="underline"
          onClick={() => toast.dismiss(id)}
          className={styles.closeBtn}
        >
          <span></span>
        </Button>
      )}
    </div>
  );
};

export { Toast };
