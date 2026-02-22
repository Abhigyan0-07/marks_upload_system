import React, { useState, useRef, useCallback } from 'react';
import Webcam from 'react-webcam';
import axios from 'axios';
import { Camera, Save, RefreshCcw, FileSpreadsheet, LayoutGrid } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const API_BASE = 'http://localhost:8000';

const Scanner: React.FC = () => {
    const webcamRef = useRef<Webcam>(null);
    const [isScanning, setIsScanning] = useState(false);
    const [results, setResults] = useState<any[]>([]);
    const [sessionSum, setSessionSum] = useState(0);
    const [grandTotal, setGrandTotal] = useState(0);
    const [status, setStatus] = useState<string>('Ready to scan');
    const [excelPath, setExcelPath] = useState('marks.xlsx');

    const capture = useCallback(async (save = false) => {
        if (!webcamRef.current) return;
        
        setIsScanning(true);
        setStatus(save ? 'Saving marks...' : 'Analyzing...');
        
        const imageSrc = webcamRef.current.getScreenshot();
        if (!imageSrc) return;

        try {
            const endpoint = save ? '/save' : '/scan';
            const response = await axios.post(`${API_BASE}${endpoint}`, {
                image_b64: imageSrc,
                excel_path: excelPath
            });

            if (response.data.success) {
                if (save) {
                    setResults(response.data.results || response.data.marks.map((m: any) => ({digit: m})));
                    setSessionSum(prev => prev + response.data.row_total);
                    setGrandTotal(response.data.grand_total);
                    setStatus(`Successfully saved: ${response.data.marks.join(', ')}`);
                } else {
                    setResults(response.data.results);
                    setStatus(`Detected: ${response.data.results.map((r: any) => r.digit).join(', ')}`);
                }
            } else {
                setStatus('No digits detected');
            }
        } catch (error) {
            console.error('Scan error:', error);
            setStatus('Error connecting to backend');
        } finally {
            setIsScanning(false);
        }
    }, [excelPath]);

    const resetSession = () => {
        setSessionSum(0);
        setResults([]);
        setStatus('Session reset');
    };

    return (
        <div className="flex flex-col gap-6 items-center w-full max-w-4xl mx-auto p-4">
            <motion.div 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="w-full relative glass overflow-hidden neon-border"
            >
                <Webcam
                    audio={false}
                    ref={webcamRef}
                    screenshotFormat="image/jpeg"
                    className="w-full aspect-video object-cover"
                />
                
                {/* Visual Guides */}
                <div className="absolute inset-0 pointer-events-none flex items-center justify-center">
                    <div className="w-[80%] h-[60%] border-2 border-dashed border-primary/50 rounded-xl relative">
                        <div className="absolute top-0 left-0 w-8 h-8 border-t-4 border-l-4 border-primary m-[-2px]"></div>
                        <div className="absolute top-0 right-0 w-8 h-8 border-t-4 border-r-4 border-primary m-[-2px]"></div>
                        <div className="absolute bottom-0 left-0 w-8 h-8 border-b-4 border-l-4 border-primary m-[-2px]"></div>
                        <div className="absolute bottom-0 right-0 w-8 h-8 border-b-4 border-r-4 border-primary m-[-2px]"></div>
                        
                        <div className="absolute -top-10 left-0 text-primary font-outfit text-sm bg-bg/60 px-2 py-1 rounded">
                            Align sheet within this zone
                        </div>
                    </div>
                </div>

                {/* Session Overlay */}
                <div className="absolute top-4 left-4 flex flex-col gap-2">
                    <div className="glass px-4 py-2 flex items-center gap-3">
                        <FileSpreadsheet className="text-primary w-5 h-5" />
                        <div>
                            <p className="text-[10px] text-text-dim uppercase tracking-wider">Session Total</p>
                            <p className="text-xl font-bold font-outfit neon-text">{sessionSum}</p>
                        </div>
                    </div>
                </div>

                {/* Status Bar */}
                <div className="absolute bottom-0 left-0 right-0 bg-bg/80 backdrop-blur px-6 py-2 border-t border-border flex justify-between items-center">
                    <span className="text-sm font-medium">{status}</span>
                    {isScanning && <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1 }}><RefreshCcw className="w-4 h-4 text-primary" /></motion.div>}
                </div>
            </motion.div>

            {/* Controls */}
            <div className="flex flex-wrap gap-4 justify-center">
                <button 
                    onClick={() => capture(false)}
                    disabled={isScanning}
                    className="btn-primary"
                >
                    <Camera className="w-5 h-5" />
                    Preview Scan
                </button>
                <button 
                    onClick={() => capture(true)}
                    disabled={isScanning}
                    className="btn-primary"
                    style={{ background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)' }}
                >
                    <Save className="w-5 h-5" />
                    Save to Excel
                </button>
                <button 
                    onClick={resetSession}
                    className="glass px-6 py-2 hover:bg-white/10 transition-colors rounded-xl flex items-center gap-2"
                >
                    <RefreshCcw className="w-4 h-4" />
                    Reset Session
                </button>
            </div>

            {/* Results Display */}
            <AnimatePresence>
                {results.length > 0 && (
                    <motion.div 
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.9 }}
                        className="w-full flex gap-3 flex-wrap justify-center mt-4"
                    >
                        {results.map((res, i) => (
                            <div key={i} className="glass-card px-6 py-4 rounded-2xl flex flex-col items-center">
                                <span className="text-3xl font-bold text-primary mb-1">{res.digit}</span>
                                <span className="text-[10px] text-text-dim uppercase">Confidence: High</span>
                            </div>
                        ))}
                    </motion.div>
                )}
            </AnimatePresence>

            <div className="mt-8 glass-card p-6 w-full max-w-2xl border-l-4 border-l-secondary">
               <h3 className="text-lg font-bold mb-2 flex items-center gap-2">
                 <LayoutGrid className="text-secondary w-5 h-5" />
                 Session Summary
               </h3>
               <div className="grid grid-cols-2 gap-4">
                 <div>
                    <p className="text-text-dim text-sm">Target File</p>
                    <p className="font-mono text-sm">{excelPath}</p>
                 </div>
                 <div>
                    <p className="text-text-dim text-sm">Grand Total (all sessions)</p>
                    <p className="font-bold text-xl neon-text">{grandTotal}</p>
                 </div>
               </div>
            </div>
        </div>
    );
};

export default Scanner;
