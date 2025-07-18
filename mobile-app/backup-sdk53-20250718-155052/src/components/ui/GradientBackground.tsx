// src/components/ui/GradientBackground.tsx
import React from 'react';
import { View, StyleSheet, ViewStyle } from 'react-native';

interface GradientBackgroundProps {
    children: React.ReactNode;
    colors?: [string, string];
    style?: ViewStyle;
    direction?: 'horizontal' | 'vertical' | 'diagonal';
}

export const GradientBackground: React.FC<GradientBackgroundProps> = ({
    children,
    colors = ['#0066CC', '#40E0D0'],
    style,
    direction = 'diagonal',
}) => {
    // Simulamos un gradiente usando múltiples capas con opacidad
    const getGradientLayers = () => {
        const [startColor, endColor] = colors;

        return (
            <View style={[StyleSheet.absoluteFillObject, { backgroundColor: startColor }]}>
                <View
                    style={[
                        StyleSheet.absoluteFillObject,
                        {
                            backgroundColor: endColor,
                            opacity: 0.7,
                            transform: direction === 'diagonal'
                                ? [{ skewX: '15deg' }]
                                : direction === 'horizontal'
                                    ? [{ translateX: 50 }]
                                    : [{ translateY: 50 }]
                        }
                    ]}
                />
                <View
                    style={[
                        StyleSheet.absoluteFillObject,
                        {
                            backgroundColor: endColor,
                            opacity: 0.3,
                            transform: direction === 'diagonal'
                                ? [{ skewX: '-10deg' }]
                                : direction === 'horizontal'
                                    ? [{ translateX: 100 }]
                                    : [{ translateY: 100 }]
                        }
                    ]}
                />
            </View>
        );
    };

    return (
        <View style={[styles.container, style]}>
            {getGradientLayers()}
            <View style={styles.content}>
                {children}
            </View>
        </View>
    );
};

const styles = StyleSheet.create({
    container: {
        position: 'relative',
        overflow: 'hidden',
    },
    content: {
        position: 'relative',
        zIndex: 1,
    },
});