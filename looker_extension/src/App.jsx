import React from 'react'
import { ExtensionProvider } from '@looker/extension-sdk-react'
import { ComponentsProvider } from '@looker/components'
import { DashboardUpdater } from './DashboardUpdater'

export const App = () => {
    return (
        <ExtensionProvider>
            <ComponentsProvider>
                <DashboardUpdater />
            </ComponentsProvider>
        </ExtensionProvider>
    )
}
