import { useState, useEffect } from 'react';
import { toast } from 'react-toastify';
import { botAPI } from '../api/botAPI';

export const useBotStatus = () => {
  const [botStatus, setBotStatus] = useState({
    status: 'stopped',
    balance: 10000,
    pnl: 0,
    positions: 0,
    lastUpdate: null,
  });
  const [isLoading, setIsLoading] = useState(false);

  const fetchStatus = async () => {
    try {
      const status = await botAPI.getStatus();
      setBotStatus(status);
    } catch (error) {
      console.error('Failed to fetch bot status:', error);
      toast.error('Failed to fetch bot status');
    }
  };

  const toggleBot = async () => {
    setIsLoading(true);
    try {
      if (botStatus.status === 'running') {
        await botAPI.stop();
        toast.success('Bot stopped successfully');
      } else {
        await botAPI.start();
        toast.success('Bot started successfully');
      }
      await fetchStatus();
    } catch (error) {
      console.error('Failed to toggle bot:', error);
      toast.error(`Failed to ${botStatus.status === 'running' ? 'stop' : 'start'} bot`);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 5000); // Update every 5 seconds
    return () => clearInterval(interval);
  }, []);

  return {
    botStatus,
    isLoading,
    toggleBot,
    refresh: fetchStatus,
  };
};