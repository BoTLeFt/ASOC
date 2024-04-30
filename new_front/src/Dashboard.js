import React, { useState, useEffect } from 'react';
import { Chart } from 'primereact/chart';

const PieChartDemo = () => {
    // Проверяем, есть ли токен в localStorage
    var token = localStorage.getItem('access_token');
    if (!token) {
        window.location.href = '/login'; // Перенаправляем на страницу аутентификации
    }
    const [statusChartData, setStatusСhartData] = useState(null);
    const [shortDescChartData, setShortDescСhartData] = useState(null);
    const [projectChartData, setProjectСhartData] = useState(null);
    const [authorChartData, setAuthorСhartData] = useState(null);
    const [severityChartData, setSeverityСhartData] = useState(null);

    const colors = ["#FA3D3A","#66BB6A","#42A5F5","#FFA726","#723D7C","#3DC606","#DDA97B","#B0F1D2","#3D9BB0","#EE0632", "#7B8891",
    "#0C7101","#BE4CED","#860BF0","#98B842","#173F60","#2BB5BC","#6BF036","#8F2D41","#294B1B","#64A4B8","#75CE75","#98527C",
    "#C23279","#CBE8AF","#7292FE","#7E37BA","#7A9A53","#BEBC75","#02A569","#97528D","#4A5FCA","#CD470E","#D4F5E0","#CFF91B"]
    useEffect(() => {
        const fetchData = async (metric) => {
            const data = await fetch(`http://host.docker.internal:8080/get_metrics?metric=${metric}`, {
                method: "GET",
                headers: {
                  'Authorization': 'Bearer ' + token,
                },
              });
            const json = await data.json();
            if (metric=='status') {
                console.log(metric);
                console.log(json);
                setStatusСhartData({
                            labels: Object.keys(json),
                            datasets: [
                                {
                                    data: Object.values(json), 
                                    backgroundColor: colors,
                                    hoverBackgroundColor: colors
                                }
                            ]
                        }
                    );
            } else if (metric=='short_desc') {
                console.log(metric);
                console.log(json);
                setShortDescСhartData({
                    labels: Object.keys(json),
                    datasets: [
                        {
                            data: Object.values(json), 
                            backgroundColor: colors,
                            hoverBackgroundColor: colors
                        }
                    ]
                });
            } else if (metric=='project') {
                console.log(metric);
                console.log(json);
                setProjectСhartData({
                    labels: Object.keys(json),
                    datasets: [
                        {
                            data: Object.values(json), 
                            backgroundColor: colors,
                            hoverBackgroundColor: colors
                        }
                    ]
                });
            } else if (metric=='author') {
                console.log(metric);
                console.log(json);
                setAuthorСhartData({
                    labels: Object.keys(json),
                    datasets: [
                        {
                            data: Object.values(json), 
                            backgroundColor: colors,
                            hoverBackgroundColor: colors
                        }
                    ]
                });
            } else if (metric=='severity') {
                console.log(metric);
                console.log(json);
                setSeverityСhartData({
                    labels: Object.keys(json),
                    datasets: [
                        {
                            data: Object.values(json), 
                            backgroundColor: colors,
                            hoverBackgroundColor: colors
                        }
                    ]
                });
            }
        }
        fetchData('status').catch((e) => {
            console.error(`An error occurred: ${e}`)
        });
        fetchData('short_desc').catch((e) => {
            console.error(`An error occurred: ${e}`)
        });
        fetchData('project').catch((e) => {
            console.error(`An error occurred: ${e}`)
        });
        fetchData('author').catch((e) => {
            console.error(`An error occurred: ${e}`)
        });
        fetchData('severity').catch((e) => {
            console.error(`An error occurred: ${e}`)
        });
    }, []);

    const [lightOptions] = useState({
        plugins: {
            legend: {
                labels: {
                    color: '#495057'
                }
            }
        }
    });
    
    return (
            <div className="dashboard">
                <Chart type="pie" data={statusChartData} options={lightOptions} style={{ position: 'relative', width: '25%' }} />
                <Chart type="pie" data={shortDescChartData} options={lightOptions} style={{ position: 'relative', width: '25%' }} />
                <Chart type="pie" data={projectChartData} options={lightOptions} style={{ position: 'relative', width: '25%' }} />
                <Chart type="pie" data={authorChartData} options={lightOptions} style={{ position: 'relative', width: '25%' }} />
                <Chart type="pie" data={severityChartData} options={lightOptions} style={{ position: 'relative', width: '25%' }} />
            </div>
    )
}

export default PieChartDemo;