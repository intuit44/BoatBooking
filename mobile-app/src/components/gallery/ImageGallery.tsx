// src/components/gallery/ImageGallery.tsx
import React, { useState } from 'react';
import { View, StyleSheet, Dimensions, TouchableOpacity } from 'react-native';
import { Text, IconButton, Surface } from 'react-native-paper';
import { SafeAreaView } from 'react-native-safe-area-context';
import { FadeInView } from '../animations/FadeInView';
import { ScaleAnimation } from '../animations/ScaleAnimation';

const { width, height } = Dimensions.get('window');

interface ImageGalleryProps {
  images: string[];
  boatName: string;
  boatType: string;
  initialIndex?: number;
  onClose: () => void;
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

// Componente de imagen placeholder para galería
const GalleryImagePlaceholder = ({
  boatName,
  boatType,
  imageIndex,
  totalImages
}: {
  boatName: string;
  boatType: string;
  imageIndex: number;
  totalImages: number;
}) => (
  <View style={styles.galleryImageContainer}>
    <View style={styles.galleryImagePlaceholder}>
      <ScaleAnimation delay={200}>
        <Text style={styles.galleryImageIcon}>{getBoatEmoji(boatType)}</Text>
      </ScaleAnimation>
      <FadeInView delay={400}>
        <Text style={styles.galleryImageText} numberOfLines={2}>{boatName}</Text>
        <Text style={styles.galleryImageSubtext}>
          Vista {imageIndex + 1} de {totalImages}
        </Text>
        <Text style={styles.galleryImageDescription}>
          {imageIndex === 0 && 'Vista principal'}
          {imageIndex === 1 && 'Vista lateral'}
          {imageIndex === 2 && 'Vista interior'}
          {imageIndex > 2 && 'Vista adicional'}
        </Text>
      </FadeInView>
    </View>
  </View>
);

export const ImageGallery: React.FC<ImageGalleryProps> = ({
  images,
  boatName,
  boatType,
  initialIndex = 0,
  onClose,
  totalImages,
}) => {
  const [currentIndex, setCurrentIndex] = useState(initialIndex);

  const handlePrevious = () => {
    setCurrentIndex((prev) => (prev > 0 ? prev - 1 : totalImages - 1));
  };

  const handleNext = () => {
    setCurrentIndex((prev) => (prev < totalImages - 1 ? prev + 1 : 0));
  };

  return (
    <SafeAreaView style={styles.container}>
      <FadeInView style={styles.content}>
        {/* Header */}
        <View style={styles.header}>
          <View style={styles.headerInfo}>
            <Text style={styles.headerTitle}>{boatName}</Text>
            <Text style={styles.headerSubtitle}>
              {currentIndex + 1} de {totalImages} fotos
            </Text>
          </View>
          <ScaleAnimation delay={100}>
            <IconButton
              icon="close"
              size={28}
              iconColor="white"
              onPress={onClose}
              style={styles.closeButton}
            />
          </ScaleAnimation>
        </View>

        {/* Main Image Area */}
        <View style={styles.imageArea}>
          <GalleryImagePlaceholder
            boatName={boatName}
            boatType={boatType}
            imageIndex={currentIndex}
            totalImages={totalImages}
          />

          {/* Navigation Arrows */}
          {totalImages > 1 && (
            <>
              <ScaleAnimation delay={300}>
                <TouchableOpacity
                  style={[styles.navButton, styles.prevButton]}
                  onPress={handlePrevious}
                >
                  <IconButton
                    icon="chevron-left"
                    size={32}
                    iconColor="white"
                  />
                </TouchableOpacity>
              </ScaleAnimation>

              <ScaleAnimation delay={400}>
                <TouchableOpacity
                  style={[styles.navButton, styles.nextButton]}
                  onPress={handleNext}
                >
                  <IconButton
                    icon="chevron-right"
                    size={32}
                    iconColor="white"
                  />
                </TouchableOpacity>
              </ScaleAnimation>
            </>
          )}
        </View>

        {/* Thumbnail Strip */}
        {totalImages > 1 && (
          <FadeInView delay={500}>
            <View style={styles.thumbnailStrip}>
              {Array.from({ length: totalImages }, (_, index) => (
                <TouchableOpacity
                  key={index}
                  style={[
                    styles.thumbnail,
                    index === currentIndex && styles.activeThumbnail
                  ]}
                  onPress={() => setCurrentIndex(index)}
                >
                  <View style={styles.thumbnailPlaceholder}>
                    <Text style={styles.thumbnailIcon}>
                      {getBoatEmoji(boatType)}
                    </Text>
                    <Text style={styles.thumbnailNumber}>
                      {index + 1}
                    </Text>
                  </View>
                </TouchableOpacity>
              ))}
            </View>
          </FadeInView>
        )}

        {/* Image Info */}
        <FadeInView delay={600}>
          <Surface style={styles.imageInfo}>
            <Text style={styles.imageInfoTitle}>
              {currentIndex === 0 && '📸 Vista Principal'}
              {currentIndex === 1 && '📐 Vista Lateral'}
              {currentIndex === 2 && '🏠 Vista Interior'}
              {currentIndex > 2 && '✨ Vista Adicional'}
            </Text>
            <Text style={styles.imageInfoDescription}>
              {currentIndex === 0 && 'Perspectiva completa de la embarcación'}
              {currentIndex === 1 && 'Detalles del diseño y estructura'}
              {currentIndex === 2 && 'Comodidades y espacios interiores'}
              {currentIndex > 2 && 'Características especiales y detalles'}
            </Text>
          </Surface>
        </FadeInView>
      </FadeInView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.95)',
  },
  content: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingTop: 10,
    paddingBottom: 20,
  },
  headerInfo: {
    flex: 1,
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: 'white',
    marginBottom: 4,
  },
  headerSubtitle: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.7)',
  },
  closeButton: {
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
  },
  imageArea: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    position: 'relative',
  },
  galleryImageContainer: {
    width: width * 0.9,
    height: height * 0.5,
    borderRadius: 12,
    overflow: 'hidden',
  },
  galleryImagePlaceholder: {
    width: '100%',
    height: '100%',
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderWidth: 2,
    borderColor: 'rgba(255, 255, 255, 0.3)',
    borderRadius: 12,
  },
  galleryImageIcon: {
    fontSize: 80,
    marginBottom: 20,
  },
  galleryImageText: {
    fontSize: 24,
    fontWeight: 'bold',
    color: 'white',
    marginBottom: 8,
    textAlign: 'center',
    paddingHorizontal: 20,
  },
  galleryImageSubtext: {
    fontSize: 16,
    color: 'rgba(255, 255, 255, 0.8)',
    textAlign: 'center',
    marginBottom: 8,
  },
  galleryImageDescription: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.6)',
    textAlign: 'center',
  },
  navButton: {
    position: 'absolute',
    top: '50%',
    width: 60,
    height: 60,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    borderRadius: 30,
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: -30,
  },
  prevButton: {
    left: 20,
  },
  nextButton: {
    right: 20,
  },
  thumbnailStrip: {
    flexDirection: 'row',
    justifyContent: 'center',
    paddingHorizontal: 20,
    paddingVertical: 20,
    gap: 12,
  },
  thumbnail: {
    width: 60,
    height: 60,
    borderRadius: 8,
    overflow: 'hidden',
    borderWidth: 2,
    borderColor: 'rgba(255, 255, 255, 0.3)',
  },
  activeThumbnail: {
    borderColor: '#0066CC',
    borderWidth: 3,
  },
  thumbnailPlaceholder: {
    width: '100%',
    height: '100%',
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
  },
  thumbnailIcon: {
    fontSize: 20,
    marginBottom: 2,
  },
  thumbnailNumber: {
    fontSize: 10,
    color: 'white',
    fontWeight: 'bold',
  },
  imageInfo: {
    margin: 20,
    padding: 16,
    borderRadius: 12,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
  },
  imageInfoTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: 'white',
    marginBottom: 4,
  },
  imageInfoDescription: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.7)',
  },
});