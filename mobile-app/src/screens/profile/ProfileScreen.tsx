import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  Alert,
  Switch
} from 'react-native';

// Datos del usuario de ejemplo
const userData = {
  name: 'Juan Pérez',
  email: 'juan.perez@email.com',
  phone: '+1 234 567 8900',
  location: 'Miami, FL',
  memberSince: '2023',
  totalBookings: 12,
  favoritesCount: 8,
  profileImage: '👤'
};

function ProfileSection({ title, children }) {
  return (
    <View style={styles.section}>
      <Text style={styles.sectionTitle}>{title}</Text>
      <View style={styles.sectionContent}>
        {children}
      </View>
    </View>
  );
}

function ProfileItem({ icon, label, value, onPress, editable = false }) {
  return (
    <TouchableOpacity 
      style={styles.profileItem} 
      onPress={onPress}
      disabled={!onPress && !editable}
    >
      <Text style={styles.profileIcon}>{icon}</Text>
      <View style={styles.profileItemContent}>
        <Text style={styles.profileLabel}>{label}</Text>
        <Text style={styles.profileValue}>{value}</Text>
      </View>
      {(onPress || editable) && (
        <Text style={styles.profileArrow}>›</Text>
      )}
    </TouchableOpacity>
  );
}

export default function ProfileScreen() {
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);
  const [locationEnabled, setLocationEnabled] = useState(true);
  const [user, setUser] = useState(userData);

  const handleEditProfile = () => {
    Alert.alert(
      'Editar Perfil',
      'Función de edición en desarrollo',
      [{ text: 'OK' }]
    );
  };

  const handleChangePassword = () => {
    Alert.alert(
      'Cambiar Contraseña',
      'Se enviará un enlace a tu email',
      [
        { text: 'Cancelar', style: 'cancel' },
        { text: 'Enviar', onPress: () => console.log('Enlace enviado') }
      ]
    );
  };

  const handleLogout = () => {
    Alert.alert(
      'Cerrar Sesión',
      '¿Estás seguro de que quieres cerrar sesión?',
      [
        { text: 'Cancelar', style: 'cancel' },
        { text: 'Cerrar Sesión', style: 'destructive', onPress: () => console.log('Logout') }
      ]
    );
  };

  const handleSupport = () => {
    Alert.alert(
      'Soporte',
      'Contacta con nosotros:\n📧 support@boatrental.com\n📞 +1 800 BOATS',
      [{ text: 'OK' }]
    );
  };

  console.log('✅ ProfileScreen cargado correctamente');

  return (
    <ScrollView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.title}>👤 Mi Perfil</Text>
        <Text style={styles.subtitle}>Gestiona tu cuenta y preferencias</Text>
      </View>

      {/* Profile Card */}
      <View style={styles.profileCard}>
        <Text style={styles.profileAvatar}>{user.profileImage}</Text>
        <View style={styles.profileInfo}>
          <Text style={styles.profileName}>{user.name}</Text>
          <Text style={styles.profileEmail}>{user.email}</Text>
          <Text style={styles.profileMember}>Miembro desde {user.memberSince}</Text>
        </View>
        <TouchableOpacity style={styles.editButton} onPress={handleEditProfile}>
          <Text style={styles.editButtonText}>Editar</Text>
        </TouchableOpacity>
      </View>

      {/* Stats */}
      <View style={styles.statsContainer}>
        <View style={styles.statItem}>
          <Text style={styles.statNumber}>{user.totalBookings}</Text>
          <Text style={styles.statLabel}>Reservas</Text>
        </View>
        <View style={styles.statItem}>
          <Text style={styles.statNumber}>{user.favoritesCount}</Text>
          <Text style={styles.statLabel}>Favoritos</Text>
        </View>
        <View style={styles.statItem}>
          <Text style={styles.statNumber}>4.8</Text>
          <Text style={styles.statLabel}>Rating</Text>
        </View>
      </View>

      {/* Information Section */}
      <ProfileSection title="📋 Información Personal">
        <ProfileItem
          icon="📧"
          label="Email"
          value={user.email}
          onPress={handleEditProfile}
        />
        <ProfileItem
          icon="📱"
          label="Teléfono"
          value={user.phone}
          onPress={handleEditProfile}
        />
        <ProfileItem
          icon="📍"
          label="Ubicación"
          value={user.location}
          onPress={handleEditProfile}
        />
        <ProfileItem
          icon="🔒"
          label="Contraseña"
          value="••••••••"
          onPress={handleChangePassword}
        />
      </ProfileSection>

      {/* Preferences Section */}
      <ProfileSection title="⚙️ Preferencias">
        <View style={styles.preferenceItem}>
          <View style={styles.preferenceInfo}>
            <Text style={styles.preferenceIcon}>🔔</Text>
            <View>
              <Text style={styles.preferenceLabel}>Notificaciones</Text>
              <Text style={styles.preferenceDescription}>Recibir ofertas y actualizaciones</Text>
            </View>
          </View>
          <Switch
            value={notificationsEnabled}
            onValueChange={setNotificationsEnabled}
            trackColor={{ false: '#ccc', true: '#0066CC' }}
          />
        </View>

        <View style={styles.preferenceItem}>
          <View style={styles.preferenceInfo}>
            <Text style={styles.preferenceIcon}>📍</Text>
            <View>
              <Text style={styles.preferenceLabel}>Ubicación</Text>
              <Text style={styles.preferenceDescription}>Permitir acceso a ubicación</Text>
            </View>
          </View>
          <Switch
            value={locationEnabled}
            onValueChange={setLocationEnabled}
            trackColor={{ false: '#ccc', true: '#0066CC' }}
          />
        </View>
      </ProfileSection>

      {/* Quick Actions */}
      <ProfileSection title="🚀 Acciones Rápidas">
        <ProfileItem
          icon="⭐"
          label="Mis Favoritos"
          value="Ver barcos guardados"
          onPress={() => console.log('Favoritos')}
        />
        <ProfileItem
          icon="📅"
          label="Historial de Reservas"
          value="Ver todas las reservas"
          onPress={() => console.log('Historial')}
        />
        <ProfileItem
          icon="💳"
          label="Métodos de Pago"
          value="Gestionar tarjetas"
          onPress={() => console.log('Pagos')}
        />
        <ProfileItem
          icon="🎁"
          label="Programa de Lealtad"
          value="Ver beneficios"
          onPress={() => console.log('Lealtad')}
        />
      </ProfileSection>

      {/* Support Section */}
      <ProfileSection title="🛟 Soporte">
        <ProfileItem
          icon="❓"
          label="Centro de Ayuda"
          value="Preguntas frecuentes"
          onPress={handleSupport}
        />
        <ProfileItem
          icon="📞"
          label="Contactar Soporte"
          value="Obtener ayuda personalizada"
          onPress={handleSupport}
        />
        <ProfileItem
          icon="⭐"
          label="Calificar la App"
          value="Déjanos tu opinión"
          onPress={() => console.log('Rating')}
        />
      </ProfileSection>

      {/* Logout */}
      <View style={styles.logoutContainer}>
        <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
          <Text style={styles.logoutButtonText}>🚪 Cerrar Sesión</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.footer}>
        <Text style={styles.footerText}>Boat Rental App v1.0.0</Text>
        <Text style={styles.footerText}>© 2025 Todos los derechos reservados</Text>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  header: {
    padding: 20,
    backgroundColor: '#0066CC',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#e3f2fd',
  },
  profileCard: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    margin: 20,
    padding: 20,
    borderRadius: 12,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  profileAvatar: {
    fontSize: 48,
    marginRight: 16,
    backgroundColor: '#f0f0f0',
    padding: 12,
    borderRadius: 30,
  },
  profileInfo: {
    flex: 1,
  },
  profileName: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 4,
  },
  profileEmail: {
    fontSize: 14,
    color: '#666',
    marginBottom: 4,
  },
  profileMember: {
    fontSize: 12,
    color: '#999',
  },
  editButton: {
    backgroundColor: '#0066CC',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
  },
  editButtonText: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 14,
  },
  statsContainer: {
    flexDirection: 'row',
    paddingHorizontal: 20,
    justifyContent: 'space-around',
    marginBottom: 20,
  },
  statItem: {
    alignItems: 'center',
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    minWidth: 80,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  statNumber: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#0066CC',
  },
  statLabel: {
    fontSize: 12,
    color: '#666',
    marginTop: 4,
  },
  section: {
    marginBottom: 20,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    paddingHorizontal: 20,
    marginBottom: 12,
  },
  sectionContent: {
    backgroundColor: '#fff',
    marginHorizontal: 20,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  profileItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  profileIcon: {
    fontSize: 20,
    marginRight: 16,
    width: 24,
    textAlign: 'center',
  },
  profileItemContent: {
    flex: 1,
  },
  profileLabel: {
    fontSize: 16,
    fontWeight: '500',
    color: '#333',
    marginBottom: 2,
  },
  profileValue: {
    fontSize: 14,
    color: '#666',
  },
  profileArrow: {
    fontSize: 20,
    color: '#ccc',
  },
  preferenceItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  preferenceInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  preferenceIcon: {
    fontSize: 20,
    marginRight: 16,
    width: 24,
    textAlign: 'center',
  },
  preferenceLabel: {
    fontSize: 16,
    fontWeight: '500',
    color: '#333',
    marginBottom: 2,
  },
  preferenceDescription: {
    fontSize: 12,
    color: '#666',
  },
  logoutContainer: {
    padding: 20,
  },
  logoutButton: {
    backgroundColor: '#F44336',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
  },
  logoutButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  footer: {
    alignItems: 'center',
    padding: 20,
  },
  footerText: {
    fontSize: 12,
    color: '#999',
    marginBottom: 4,
  },
});
