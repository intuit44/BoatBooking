// src/components/animations/ScaleAnimation.tsx
import React, { useEffect, useRef } from 'react';
import { Animated, ViewStyle } from 'react-native';

interface ScaleAnimationProps {
  children: React.ReactNode;
  delay?: number;
  duration?: number;
  initialScale?: number;
  finalScale?: number;
  style?: ViewStyle;
}

export const ScaleAnimation: React.FC<ScaleAnimationProps> = ({
  children,
  delay = 0,
  duration = 400,
  initialScale = 0.8,
  finalScale = 1,
  style,
}) => {
  const scaleAnim = useRef(new Animated.Value(initialScale)).current;
  const fadeAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    const timer = setTimeout(() => {
      Animated.parallel([
        Animated.spring(scaleAnim, {
          toValue: finalScale,
          tension: 100,
          friction: 8,
          useNativeDriver: true,
        }),
        Animated.timing(fadeAnim, {
          toValue: 1,
          duration,
          useNativeDriver: true,
        }),
      ]).start();
    }, delay);

    return () => clearTimeout(timer);
  }, [scaleAnim, fadeAnim, delay, duration, finalScale]);

  return (
    <Animated.View
      style={[
        {
          opacity: fadeAnim,
          transform: [{ scale: scaleAnim }],
        },
        style,
      ]}
    >
      {children}
    </Animated.View>
  );
};