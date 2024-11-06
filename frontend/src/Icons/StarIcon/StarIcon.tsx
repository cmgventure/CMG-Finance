import { FC } from 'react';

interface IStarIconProps {
  stroke?: string;
  width: string;
  height: string;
}

const StarIcon: FC<IStarIconProps> = (props) => {
  const { stroke, width, height } = props;
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width={width}
      height={height}
      viewBox="0 0 20 20"
      fill="none"
    >
      <path
        d="M10.0007 0.833008L12.8332 6.57134L19.1673 7.49717L14.584 11.9613L15.6657 18.268L10.0007 15.2888L4.33565 18.268L5.41732 11.9613L0.833984 7.49717L7.16815 6.57134L10.0007 0.833008Z"
        stroke={stroke ?? '#98A2B3'}
        strokeWidth="1.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
};

export default StarIcon;
