function MainChart({ data }) {

    return (
        <section className="chart-card">

            <div className="chart-header">
                <div>
                    <h2>Questions by Crop</h2>

                    <p>
                        Most frequently discussed crops
                    </p>
                </div>
            </div>

            <div className="bar-chart">

                {data?.map((item) => (

                    <div
                        className="bar-item"
                        key={item.crop}
                    >

                        <div className="bar-label">
                            {item.crop}
                        </div>

                        <div className="bar-container">

                            <div
                                className="bar"
                                style={{
                                    width: `${item.percentage}%`
                                }}
                            />

                        </div>

                        <div className="bar-value">
                            {item.count}
                        </div>

                    </div>

                ))}

            </div>

        </section>
    );
}

export default MainChart;