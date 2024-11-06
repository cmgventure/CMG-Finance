import { FC } from 'react';

interface ITrashIconProps {
  stroke?: string;
}

const TrashIcon: FC<ITrashIconProps> = (props) => {
  const { stroke } = props;
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="20" fill="none">
      <path
        d="M1.5 5.00008H3.16667M3.16667 5.00008H16.5M3.16667 5.00008V16.6667C3.16667 17.1088 3.34226 17.5327 3.65482 17.8453C3.96738 18.1578 4.39131 18.3334 4.83333 18.3334H13.1667C13.6087 18.3334 14.0326 18.1578 14.3452 17.8453C14.6577 17.5327 14.8333 17.1088 14.8333 16.6667V5.00008H3.16667ZM5.66667 5.00008V3.33341C5.66667 2.89139 5.84226 2.46746 6.15482 2.1549C6.46738 1.84234 6.89131 1.66675 7.33333 1.66675H10.6667C11.1087 1.66675 11.5326 1.84234 11.8452 2.1549C12.1577 2.46746 12.3333 2.89139 12.3333 3.33341V5.00008M7.33333 9.16675V14.1667M10.6667 9.16675V14.1667"
        stroke={stroke ?? '#667085'}
        strokeWidth="1.66667"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
};

export default TrashIcon;
