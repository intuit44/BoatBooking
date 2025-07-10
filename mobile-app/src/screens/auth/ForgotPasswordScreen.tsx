// File: mobile-app/src/screens/auth/ForgotPasswordScreen.tsx
import React, { useState } from 'react';
import {
    View,
    StyleSheet,
    ScrollView,
    KeyboardAvoidingView,
    Platform,
    Alert,
} from 'react-native';
import {
    Text,
    TextInput,
    Button,
    Card,
    Title,
    Paragraph,
} from 'react-native-paper';
import { useAppDispatch, useAppSelector } from '../../store/hooks';
import { forgotPassword } from '../../store/slices/authSlice';
import { RootState } from '../../store/store';

interface Props {
    navigation: any;
}

export function ForgotPasswordScreen({ navigation }: Props) {
    const [email, setEmail] = useState('');
    const dispatch = useAppDispatch();
    const { isLoading } = useAppSelector((state: RootState) => state.auth);

    const handleForgotPassword = async () => {
        if (!email) {
            Alert.alert('Error', 'Por favor ingresa tu email');
            return;
        }

        try {
            await dispatch(forgotPassword(email)).unwrap();
            Alert.alert(
                'Éxito',
                'Se ha enviado un código de verificación a tu email',
                [{ text: 'OK', onPress: () => navigation.goBack() }]
            );
        } catch (error) {
            Alert.alert('Error', 'No se pudo enviar el código de verificación');
        }
    };

    return (
        <KeyboardAvoidingView
            style={styles.container}
            behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        >
            <ScrollView contentContainerStyle={styles.scrollContainer}>
                <View style={styles.header}>
                    <Title style={styles.title}>🔐 Recuperar Contraseña</Title>
                    <Paragraph style={styles.subtitle}>
                        Ingresa tu email para recibir un código de verificación
                    </Paragraph>
                </View>

                <Card style={styles.card}>
                    <Card.Content>
                        <TextInput
                            label="Email"
                            value={email}
                            onChangeText={setEmail}
                            mode="outlined"
                            keyboardType="email-address"
                            autoCapitalize="none"
                            style={styles.input}
                        />

                        <Button
                            mode="contained"
                            onPress={handleForgotPassword}
                            loading={isLoading}
                            disabled={isLoading}
                            style={styles.button}
                        >
                            Enviar Código
                        </Button>

                        <Button
                            mode="text"
                            onPress={() => navigation.goBack()}
                            style={styles.linkButton}
                        >
                            Volver al Login
                        </Button>
                    </Card.Content>
                </Card>
            </ScrollView>
        </KeyboardAvoidingView>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#f5f5f5',
    },
    scrollContainer: {
        flexGrow: 1,
        justifyContent: 'center',
        padding: 20,
    },
    header: {
        alignItems: 'center',
        marginBottom: 30,
    },
    title: {
        fontSize: 28,
        fontWeight: 'bold',
        color: '#0066CC',
        marginBottom: 8,
    },
    subtitle: {
        fontSize: 16,
        color: '#666',
        textAlign: 'center',
    },
    card: {
        elevation: 4,
        marginBottom: 20,
    },
    input: {
        marginBottom: 16,
    },
    button: {
        marginTop: 10,
        paddingVertical: 8,
    },
    linkButton: {
        marginTop: 10,
    },
});

export default ForgotPasswordScreen;
