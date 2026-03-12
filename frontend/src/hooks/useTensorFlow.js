import { useState, useEffect } from 'react';
import * as mobilenet from '@tensorflow-models/mobilenet';
import '@tensorflow/tfjs';

const useTensorFlow = () => {
  const [model, setModel] = useState(null);
  const [isReady, setIsReady] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    const loadModel = async () => {
      try {
        const loadedModel = await mobilenet.load();
        setModel(loadedModel);
        setIsReady(true);
        console.log('Modelo MobileNet cargado correctamente');
      } catch (err) {
        console.error('Error cargando modelo:', err);
        setError('Error cargando el modelo de IA');
      }
    };

    loadModel();
  }, []);

  return { model, isReady, error };
};

export default useTensorFlow;
