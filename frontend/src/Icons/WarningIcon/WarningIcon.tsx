import { FC } from 'react';

interface IGeneratingIconProps {
  stroke?: string;
}

const WarningIcon: FC<IGeneratingIconProps> = (props) => {
  const { stroke } = props;
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" fill="none">
      <path
        d="M11 7V11M11 15H11.01M21 11C21 16.5228 16.5228 21 11 21C5.47715 21 1 16.5228 1 11C1 5.47715 5.47715 1 11 1C16.5228 1 21 5.47715 21 11Z"
        stroke={stroke ?? '#DC6803'}
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
};

export default WarningIcon;
