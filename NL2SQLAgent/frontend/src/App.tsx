import { ConfigProvider, theme } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import { ChatSidebar } from './components/ChatSidebar'
import { ChatArea } from './components/ChatArea'
import { ChartPanel } from './components/ChartPanel'
import styles from './App.module.css'

function App() {
  return (
    <ConfigProvider
      locale={zhCN}
      theme={{
        algorithm: theme.darkAlgorithm,
        token: {
          colorPrimary: '#00f0ff',
          colorBgContainer: '#111126',
          colorBgElevated: '#1a1a3e',
          colorBorder: 'rgba(0, 240, 255, 0.12)',
          colorText: '#e0e0ff',
          colorTextSecondary: '#8888aa',
          colorTextTertiary: '#555577',
          fontFamily: "'Rajdhani', -apple-system, BlinkMacSystemFont, sans-serif",
          borderRadius: 6,
        },
        components: {
          Table: {
            headerBg: 'rgba(0, 240, 255, 0.06)',
            headerColor: '#00a8b3',
            rowHoverBg: 'rgba(0, 240, 255, 0.03)',
            borderColor: 'rgba(0, 240, 255, 0.06)',
            colorBgContainer: '#111126',
            colorText: '#8888aa',
            fontSize: 13,
          },
          Tag: {
            defaultBg: 'rgba(0, 240, 255, 0.08)',
            defaultColor: '#00f0ff',
          },
          Button: {
            borderRadius: 6,
          },
          Input: {
            colorBgContainer: '#111126',
            activeBorderColor: '#00f0ff',
            hoverBorderColor: 'rgba(0, 240, 255, 0.3)',
          },
        },
      }}
    >
      <div className={styles.layout}>
        <div className={styles.sidebar}>
          <ChatSidebar />
        </div>
        <div className={styles.main}>
          <ChatArea />
        </div>
        <div className={styles.chart}>
          <ChartPanel />
        </div>
      </div>
    </ConfigProvider>
  )
}

export default App
