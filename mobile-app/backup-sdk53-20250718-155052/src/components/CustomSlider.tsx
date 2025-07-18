import React from 'react';
import { ViewStyle } from 'react-native';
import RNSlider from '@react-native-community/slider';

interface CustomSliderProps {
  style?: ViewStyle;
  minimumValue: number;
  maximumValue: number;
  value: number;
  onValueChange: (value: number) => void;
  step?: number;
  minimumTrackTintColor?: string;
  maximumTrackTintColor?: string;
}

export const CustomSlider: React.FC<CustomSliderProps> = ({
  style,
  minimumValue,
  maximumValue,
  value,
  onValueChange,
  step,
  minimumTrackTintColor,
  maximumTrackTintColor,
}) => {
  return (
    <RNSlider
      style={style}
      minimumValue={minimumValue}
      maximumValue={maximumValue}
      value={value}
      onValueChange={onValueChange}
      step={step}
      minimumTrackTintColor={minimumTrackTintColor}
      maximumTrackTintColor={maximumTrackTintColor}
    />
  );
};