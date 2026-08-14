import Card from "./Card"
import DashboardHeader from "./DashboardHeader"
import SummaryCards from "./SummaryCards"
function Dashboard(){
    return (
        <>
        <main className="dashboard">

            <DashboardHeader />

            <SummaryCards />

            <section className="dashboard-charts">

                {/* <QuestionTrend />

                <TopicBreakdown /> */}

            </section>

        </main>
        </>
    )
}

export default Dashboard