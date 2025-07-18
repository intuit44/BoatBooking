// src/components/gallery/AnimatedImageCarousel.tsx
import React, { useState } from 'react';
import { View, StyleSheet, ScrollView, Dimensions, TouchableOpacity } from 'react-native';
import { Text } from 'react-native-paper';
import { FadeInView } from '../animations/FadeInView';
import { ScaleAnimation } from '../animations/ScaleAnimation';

const { width } = Dimensions.get('window');

interface AnimatedImageCarouselProps {
  images: string[];
  boatName: string;
  boatType: string;
  onImagePress: () => void;
  onIndexChange: (index: number) => void;
  totalImages: number;
}

// Función para obtener emoji del tipo de embarcación
const getBoatEmoji = (type: string) => {
  const emojiMap = {
    yacht: '🛥️',
    sailboat: '⛵',
    motorboat: '🚤',
    catamaran: '🛥️',
    jetski: '🏄'
  };
  return emojiMap[type as keyof typeof emojiMap] || '🚤';
};

// Componente de imagen placeholder animado
const AnimatedImagePlaceholder = ({
  boatName,
  boatType,
  imageIndex,
  totalImages,
  onPress
}: {
  boatName: string;
  boatType: string;
  imageIndex: number;
  totalImages: number;
  onPress: () => void;
}) => (
  <TouchableOpacity onPress={onPress} activeOpacity={0.9}>
    <View style={styles.imageContainer}>
      <View style={styles.imagePlaceholder}>
        <ScaleAnimation delay={imageIndex * 100}>
          <Text style={styles.imageIcon}>{getBoatEmoji(boatType)}</Text>
        </ScaleAnimation>
        <FadeInView delay={200 + (imageIndex * 100)}>
          <Text style={styles.imageName} numberOfLines={2}>{boatName}</Text>
          <Text style={styles.imageSubtext}>
            Imagen {imageIndex + 1} de {totalImages}
          </Text>
          <View style={styles.tapHint}>
            <Text style={styles.tapHintText}>👆 Toca para galería</Text>
          </View>
        </FadeInView>

        {/* Decorative elements */}
        <View style={styles.decorativeElements}>
          <View style={[styles.decorativeCircle, { top: 20, left: 20 }]} />
          <View style={[styles.decorativeCircle, { bottom: 20, right: 20 }]} />
          <View style={[styles.decorativeLine, { top: '50%', left: 10 }]} />
          <View style={[styles.decorativeLine, { top: '50%', right: 10 }]} />
        </View>
      </View>
    </View>
  </TouchableOpacity>
);

export const AnimatedImageCarousel: React.FC<AnimatedImageCarouselProps> = ({
  images,
  boatName,
  boatType,
  onImagePress,
  onIndexChange,
  totalImages,
}) => {
  const [currentIndex, setCurrentIndex] = useState(0);

  const handleScroll = (event: any) => {
    const index = Math.round(event.nativeEvent.contentOffset.x / width);
    setCurrentIndex(index);
    onIndexChange(index);
  };

  return (
    <View style={styles.container}>
      <ScrollView
        horizontal
        pagingEnabled
        showsHorizontalScrollIndicator={false}
        onMomentumScrollEnd={handleScroll}
        scrollEventThrottle={16}
      >
        {Array.from({ length: totalImages }, (_, index) => (
          <AnimatedImagePlaceholder
            key={index}
            boatName={boatName}
            boatType={boatType}
            imageIndex={index}
            totalImages={totalImages}
            onPress={onImagePress}
          />
        ))}
      </ScrollView>

      {/* Image Indicators with Animation */}
      <View style={styles.indicatorsContainer}>
        {Array.from({ length: totalImages }, (_, index) => (
          <ScaleAnimation key={index} delay={500 + (index * 50)}>
            <View
              style={[
                styles.indicator,
                index === currentIndex && styles.activeIndicator
              ]}
            />
          </ScaleAnimation>
        ))}
      </View>

      {/* Image Counter */}
      <FadeInView delay={600}>
        <View style={styles.counterContainer}>
          <Text style={styles.counterText}>
            {currentIndex + 1} / {totalImages}
          </Text>
        </View>
      </FadeInView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    position: 'relative',
  },
  imageContainer: {
    width,
    height: 300,
  },
  imagePlaceholder: {
    width: '100%',
    height: '100%',
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#E3F2FD',
    position: 'relative',
    overflow: 'hidden',
  },
  imageIcon: {
    fontSize: 60,
    marginBottom: 12,
    textShadowColor: 'rgba(0, 0, 0, 0.1)',
    textShadowOffset: { width: 1, height: 1 },
    textShadowRadius: 2,
  },
  imageName: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#0066CC',
    marginBottom: 4,
    textAlign: 'center',
    paddingHorizontal: 20,
    textShadowColor: 'rgba(255, 255, 255, 0.8)',
    textShadowOffset: { width: 1, height: 1 },
    textShadowRadius: 2,
  },
  imageSubtext: {
    fontSize: 14,
    color: '#666',
    textAlign: 'center',
    marginBottom: 12,
  },
  tapHint: {
    backgroundColor: 'rgba(0, 102, 204, 0.9)',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    position: 'absolute',
    bottom: 30,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 4,
    elevation: 5,
  },
  tapHintText: {
    color: 'white',
    fontSize: 12,
    fontWeight: 'bold',
  },
  decorativeElements: {
    position: 'absolute',
    width: '100%',
    height: '100%',
  },
  decorativeCircle: {
    position: 'absolute',
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(0, 102, 204, 0.1)',
    borderWidth: 2,
    borderColor: 'rgba(0, 102, 204, 0.3)',
  },
  decorativeLine: {
    position: 'absolute',
    width: 30,
    height: 2,
    backgroundColor: 'rgba(0, 102, 204, 0.2)',
    marginTop: -1,
  },
  indicatorsContainer: {
    position: 'absolute',
    bottom: 16,
    left: 0,
    right: 0,
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 8,
  },
  indicator: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: 'rgba(255, 255, 255, 0.5)',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.8)',
  },
  activeIndicator: {
    backgroundColor: 'white',
    borderColor: '#0066CC',
    borderWidth: 2,
    transform: [{ scale: 1.2 }],
  },
  counterContainer: {
    position: 'absolute',
    top: 16,
    right: 16,
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
  },
  counterText: {
    color: 'white',
    fontSize: 12,
    fontWeight: 'bold',
  },
});