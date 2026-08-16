import { useEffect, useState } from "react";
import { getAnalytics } from "../../../services/chatApi";
import Card from "./Card"
import DashboardHeader from "./DashboardHeader"
import MainChart from "./MainChart"
import StatsSection from "./StatsSection"

function Dashboard(){
    const [analytics, setAnalytics] = useState(null);
    const [loading, setLoading] = useState(true);

     useEffect(() => {

        async function loadAnalytics() {

            try {

                const data = await getAnalytics();

                setAnalytics(data);

            } catch (error) {

                console.error(
                    "Unable to load analytics:",
                    error
                );

            } finally {

                setLoading(false);
            }
        }

        loadAnalytics();

    }, []);

    if (loading) {
        return <p>Loading dashboard...</p>;
    }
    
    return (
        <>
        <main className="dashboard">

            <DashboardHeader />
            
            <section className="dashboard-cards">
                <StatsSection/>
            </section>

            <section className="dashboard-charts">
                <MainChart/>
            </section>

        </main>
        </>
    )
}

export default Dashboard