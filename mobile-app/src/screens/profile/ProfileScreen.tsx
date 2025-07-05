import React, { useState } from 'react';
import { View, StyleSheet, ScrollView, Alert } from 'react-native';
import {
  Text,
  Card,
  Title,
  Paragraph,
  Button,
  Avatar,
  List,
  Switch,
  Divider,
  Surface,
  IconButton,
  TextInput,
  Dialog,
  Portal,
} from 'react-native-paper';
import { useAppDispatch } from '../../store/hooks';
import { AppDispatch, RootState } from '../../store/store';
import { logout, updateProfile } from '../../store/slices/authSlice';
import { useSelector } from 'react-redux';

interface Props {
  navigation: any;
}

export function ProfileScreen({ navigation }: Props) {
  const dispatch = useAppDispatch();
  const { user } = useSelector((state: RootState) => state.auth);

  const [notifications, setNotifications] = useState(true);
  const [locationServices, setLocationServices] = useState(true);
  const [emailMarketing, setEmailMarketing] = useState(false);
  const [editDialogVisible, setEditDialogVisible] = useState(false);
  const [editData, setEditData] = useState({
    name: user?.name || '',
    phone: user?.phone || '',
    email: user?.email || '',
  });

  const handleLogout = () => {
    Alert.alert(
      'Cerrar Sesión',
      '¿Estás seguro que deseas cerrar sesión?',
      [
        { text: 'Cancelar', style: 'cancel' },
        {
          text: 'Cerrar Sesión',
          style: 'destructive',
          onPress: () => dispatch(logout())
        },
      ]
    );
  };

  const handleSaveProfile = () => {
    dispatch(updateProfile(editData));
    setEditDialogVisible(false);
    Alert.alert('Éxito', 'Perfil actualizado correctamente');
  };

  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map(word => word[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  return (
    <ScrollView style={styles.container}>
      {/* Header */}
      <Surface style={styles.header}>
        <View style={styles.headerContent}>
          <Title style={styles.headerTitle}>👤 Mi Perfil</Title>
          <IconButton
            icon="cog"
            size={24}
            onPress={() => {/* TODO: Settings */ }}
          />
        </View>
      </Surface>

      {/* Profile Card */}
      <Card style={styles.profileCard}>
        <Card.Content>
          <View style={styles.profileHeader}>
            <Avatar.Text
              size={80}
              label={getInitials(user?.name || 'Usuario')}
              style={styles.avatar}
            />
            <View style={styles.profileInfo}>
              <Title style={styles.userName}>{user?.name || 'Usuario'}</Title>
              <Paragraph style={styles.userEmail}>{user?.email}</Paragraph>
              <Paragraph style={styles.userPhone}>📱 {user?.phone}</Paragraph>
            </View>
            <IconButton
              icon="pencil"
              size={20}
              onPress={() => setEditDialogVisible(true)}
            />
          </View>

          <View style={styles.statsContainer}>
            <View style={styles.statItem}>
              <Text style={styles.statNumber}>12</Text>
              <Text style={styles.statLabel}>Reservas</Text>
            </View>
            <View style={styles.statItem}>
              <Text style={styles.statNumber}>4.8</Text>
              <Text style={styles.statLabel}>⭐ Rating</Text>
            </View>
            <View style={styles.statItem}>
              <Text style={styles.statNumber}>2</Text>
              <Text style={styles.statLabel}>Años</Text>
            </View>
          </View>
        </Card.Content>
      </Card>

      {/* Quick Actions */}
      <Card style={styles.actionsCard}>
        <Card.Content>
          <Title style={styles.sectionTitle}>🚀 Acciones Rápidas</Title>
          <View style={styles.quickActions}>
            <Button
              mode="contained"
              icon="calendar-plus"
              onPress={() => navigation.navigate('Search')}
              style={styles.quickButton}
            >
              Nueva Reserva
            </Button>
            <Button
              mode="outlined"
              icon="history"
              onPress={() => navigation.navigate('Bookings')}
              style={styles.quickButton}
            >
              Mis Reservas
            </Button>
          </View>
        </Card.Content>
      </Card>

      {/* Menu Options */}
      <Card style={styles.menuCard}>
        <Card.Content>
          <Title style={styles.sectionTitle}>⚙️ Configuración</Title>

          <List.Item
            title="Notificaciones Push"
            description="Recibir alertas de reservas y ofertas"
            left={props => <List.Icon {...props} icon="bell" />}
            right={() => (
              <Switch
                value={notifications}
                onValueChange={setNotifications}
              />
            )}
          />

          <Divider />

          <List.Item
            title="Servicios de Ubicación"
            description="Encontrar marinas cercanas"
            left={props => <List.Icon {...props} icon="map-marker" />}
            right={() => (
              <Switch
                value={locationServices}
                onValueChange={setLocationServices}
              />
            )}
          />

          <Divider />

          <List.Item
            title="Marketing por Email"
            description="Ofertas especiales y promociones"
            left={props => <List.Icon {...props} icon="email" />}
            right={() => (
              <Switch
                value={emailMarketing}
                onValueChange={setEmailMarketing}
              />
            )}
          />
        </Card.Content>
      </Card>

      {/* Support & Info */}
      <Card style={styles.menuCard}>
        <Card.Content>
          <Title style={styles.sectionTitle}>🆘 Soporte</Title>

          <List.Item
            title="Centro de Ayuda"
            description="Preguntas frecuentes y guías"
            left={props => <List.Icon {...props} icon="help-circle" />}
            right={props => <List.Icon {...props} icon="chevron-right" />}
            onPress={() => {/* TODO: Help Center */ }}
          />

          <Divider />

          <List.Item
            title="Contactar Soporte"
            description="Chat en vivo y WhatsApp"
            left={props => <List.Icon {...props} icon="message" />}
            right={props => <List.Icon {...props} icon="chevron-right" />}
            onPress={() => {/* TODO: Contact Support */ }}
          />

          <Divider />

          <List.Item
            title="Términos y Condiciones"
            description="Políticas de uso y privacidad"
            left={props => <List.Icon {...props} icon="file-document" />}
            right={props => <List.Icon {...props} icon="chevron-right" />}
            onPress={() => {/* TODO: Terms */ }}
          />

          <Divider />

          <List.Item
            title="Calificar App"
            description="Ayúdanos a mejorar"
            left={props => <List.Icon {...props} icon="star" />}
            right={props => <List.Icon {...props} icon="chevron-right" />}
            onPress={() => {/* TODO: Rate App */ }}
          />
        </Card.Content>
      </Card>

      {/* App Info */}
      <Card style={styles.infoCard}>
        <Card.Content>
          <View style={styles.appInfo}>
            <Text style={styles.appName}>🛥️ Boat Rentals Venezuela</Text>
            <Text style={styles.appVersion}>Versión 1.0.0</Text>
            <Text style={styles.appDescription}>
              La mejor app para alquilar embarcaciones en Venezuela 🇻🇪
            </Text>
          </View>
        </Card.Content>
      </Card>

      {/* Logout Button */}
      <View style={styles.logoutContainer}>
        <Button
          mode="outlined"
          icon="logout"
          onPress={handleLogout}
          style={styles.logoutButton}
          textColor="#F44336"
        >
          Cerrar Sesión
        </Button>
      </View>

      {/* Edit Profile Dialog */}
      <Portal>
        <Dialog visible={editDialogVisible} onDismiss={() => setEditDialogVisible(false)}>
          <Dialog.Title>✏️ Editar Perfil</Dialog.Title>
          <Dialog.Content>
            <TextInput
              label="Nombre Completo"
              value={editData.name}
              onChangeText={(text) => setEditData({ ...editData, name: text })}
              mode="outlined"
              style={styles.dialogInput}
            />
            <TextInput
              label="Teléfono"
              value={editData.phone}
              onChangeText={(text) => setEditData({ ...editData, phone: text })}
              mode="outlined"
              keyboardType="phone-pad"
              style={styles.dialogInput}
            />
            <TextInput
              label="Email"
              value={editData.email}
              onChangeText={(text) => setEditData({ ...editData, email: text })}
              mode="outlined"
              keyboardType="email-address"
              style={styles.dialogInput}
            />
          </Dialog.Content>
          <Dialog.Actions>
            <Button onPress={() => setEditDialogVisible(false)}>Cancelar</Button>
            <Button onPress={handleSaveProfile}>Guardar</Button>
          </Dialog.Actions>
        </Dialog>
      </Portal>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  header: {
    elevation: 4,
    backgroundColor: 'white',
  },
  headerContent: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    paddingTop: 60,
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
  },
  profileCard: {
    margin: 16,
    elevation: 4,
  },
  profileHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 20,
  },
  avatar: {
    backgroundColor: '#0066CC',
  },
  profileInfo: {
    flex: 1,
    marginLeft: 16,
  },
  userName: {
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  userEmail: {
    fontSize: 14,
    color: '#666',
    marginBottom: 2,
  },
  userPhone: {
    fontSize: 14,
    color: '#666',
  },
  statsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: '#E0E0E0',
  },
  statItem: {
    alignItems: 'center',
  },
  statNumber: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#0066CC',
  },
  statLabel: {
    fontSize: 12,
    color: '#666',
    marginTop: 4,
  },
  actionsCard: {
    marginHorizontal: 16,
    marginBottom: 16,
    elevation: 2,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 12,
  },
  quickActions: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  quickButton: {
    flex: 1,
    marginHorizontal: 4,
  },
  menuCard: {
    marginHorizontal: 16,
    marginBottom: 16,
    elevation: 2,
  },
  infoCard: {
    marginHorizontal: 16,
    marginBottom: 16,
    backgroundColor: '#E3F2FD',
    elevation: 2,
  },
  appInfo: {
    alignItems: 'center',
  },
  appName: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#0066CC',
    marginBottom: 4,
  },
  appVersion: {
    fontSize: 14,
    color: '#666',
    marginBottom: 8,
  },
  appDescription: {
    fontSize: 14,
    color: '#666',
    textAlign: 'center',
  },
  logoutContainer: {
    padding: 16,
    paddingBottom: 32,
  },
  logoutButton: {
    borderColor: '#F44336',
  },
  dialogInput: {
    marginBottom: 12,
  },
});