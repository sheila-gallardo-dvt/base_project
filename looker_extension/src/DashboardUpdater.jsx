import React, { useState, useCallback } from 'react'
import {
    ExtensionContext,
} from '@looker/extension-sdk-react'
import {
    Box,
    Button,
    FieldText,
    Heading,
    MessageBar,
    Paragraph,
    SpaceVertical,
    Spinner,
    Icon,
} from '@looker/components'

const CLOUD_FUNCTION_URL = process.env.REACT_APP_CLOUD_FUNCTION_URL || ''

export const DashboardUpdater = () => {
    const [dashboardId, setDashboardId] = useState('')
    const [loading, setLoading] = useState(false)
    const [message, setMessage] = useState(null) // { type, text }

    const handleSubmit = useCallback(async () => {
        if (!dashboardId.trim()) {
            setMessage({ type: 'critical', text: 'Introduce un Dashboard ID.' })
            return
        }

        setLoading(true)
        setMessage(null)

        try {
            // Opción A: Llamar directamente a la Cloud Function
            if (CLOUD_FUNCTION_URL) {
                const resp = await fetch(`${CLOUD_FUNCTION_URL}/execute`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        form_params: {
                            dashboard_id: dashboardId.trim(),
                            confirm: 'yes',
                        },
                    }),
                })

                const data = await resp.json()
                if (data.looker?.success) {
                    setMessage({
                        type: 'positive',
                        text: `✅ ${data.looker.message}. Revisa GitHub Actions para ver el progreso.`,
                    })
                    setDashboardId('')
                } else {
                    setMessage({
                        type: 'critical',
                        text: `❌ ${data.looker?.message || 'Error desconocido'}`,
                    })
                }
            } else {
                setMessage({
                    type: 'warn',
                    text: 'No se ha configurado la URL de la Cloud Function. Configura REACT_APP_CLOUD_FUNCTION_URL.',
                })
            }
        } catch (err) {
            setMessage({ type: 'critical', text: `Error de conexión: ${err.message}` })
        } finally {
            setLoading(false)
        }
    }, [dashboardId])

    return (
        <Box p="xlarge" maxWidth="600px" mx="auto" mt="xlarge">
            <SpaceVertical gap="large">
                <Box textAlign="center">
                    <Heading fontSize="xlarge" fontWeight="bold" mb="small">
                        🔄 Actualizar Dashboard LookML
                    </Heading>
                    <Paragraph color="text2" fontSize="small">
                        Introduce el ID del dashboard de Looker para importar o actualizar
                        su código en el base_project.
                    </Paragraph>
                </Box>

                <FieldText
                    label="Dashboard ID"
                    description="Encuéntralo en la URL del dashboard de Looker"
                    placeholder="Ej: 42"
                    value={dashboardId}
                    onChange={(e) => setDashboardId(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
                    disabled={loading}
                />

                <Button
                    onClick={handleSubmit}
                    disabled={loading || !dashboardId.trim()}
                    fullWidth
                    size="large"
                    color="key"
                >
                    {loading ? (
                        <>
                            <Spinner size={20} mr="xsmall" />
                            Ejecutando...
                        </>
                    ) : (
                        '🚀 Actualizar Dashboard'
                    )}
                </Button>

                {message && (
                    <MessageBar intent={message.type} onPrimaryClick={() => setMessage(null)}>
                        {message.text}
                    </MessageBar>
                )}
            </SpaceVertical>
        </Box>
    )
}
