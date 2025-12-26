import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
df = pd.read_csv("careers360_colleges.csv")
df.drop_duplicates(subset=['title'], inplace=True)
df.dropna(subset=['rating','course_fee_inr'], inplace=True)
print(df.head())

#KPI Summary
total_colleges = df['title'].nunique()
avg_rating = df['rating'].mean()
avg_fee = df['course_fee_inr'].mean()
print(f"Total Colleges: {total_colleges}")
print(f"Avg Rating: {avg_rating:.2f}")
print(f"Avg Course Fee (INR): {avg_fee:,.0f}")

#Bar Chart - Top 10 states by Number of colleges
top_states = df['state'].value_counts().head(10)
plt.figure(figsize = (10,6))
plt.barh(top_states.index, top_states.values,color='skyblue')
plt.title("Top 10 States by number of colleges",fontsize = 14)
plt.xlabel("Number of Colleges")
plt.ylabel("State")
plt.gca().invert_yaxis()
plt.tight_layout()
plt.show()

#Donut Chart - College Distribution by Domain
domain_count = df['domain'].value_counts()
plt.figure(figsize=(6,6))
wedges, texts, autotexts = plt.pie(domain_count,labels=domain_count.index,autopct='%1.1f%%',startangle=140)
centre_circle = plt.Circle((0,0), 0.70, color='white')
fig = plt.gcf()
fig.gca().add_artist(centre_circle)
plt.title("College Distribution by Domain",fontsize = 14)
plt.tight_layout()
plt.show()

#Top 10 colleges by Average Rating
top_colleges = df.groupby('title')['rating'].mean().sort_values(ascending=False).head(10)
plt.figure(figsize = (10,6))
plt.barh(top_colleges.index, top_colleges.values,color='lightgreen')
plt.title("Top 10 Colleges by Rating", fontsize = 14)
plt.xlabel("Average Rating")
plt.ylabel("College")
plt.gca().invert_yaxis()
plt.tight_layout()
plt.show()


#Average Course Fee by Domain
avg_fee_domain = df.groupby('domain')['course_fee_inr'].mean().sort_values()
plt.figure(figsize = (10,6))
plt.barh(avg_fee_domain.index, avg_fee_domain.values,color='salmon')
plt.title("Average Course Fee by Domain", fontsize = 14)
plt.xlabel("Average Course Fee (INR)")
plt.ylabel("Domain")
plt.tight_layout()
plt.show()

#Course Count by State and Domain (Clustered Bars)
state_domain = df.groupby(['state','domain']).size().unstack(fill_value=0)
top_states = state_domain.sum(axis=1).sort_values(ascending=False).head(8).index
state_domain = state_domain.loc[top_states]
x = np.arange(len(state_domain.index))
width = 0.15
plt.figure(figsize = (12,6))
for i,col in enumerate(state_domain.columns):
    plt.bar(x + i * width, state_domain[col], width=width, label=col)
plt.title("Course Count by state and Domain",fontsize = 14)
plt.xlabel("State")
plt.ylabel("Number of Courses")
plt.xticks(x + width, state_domain.index, rotation=45)
plt.legend(title="Domain",bbox_to_anchor=(1.05,1))
plt.tight_layout()
plt.show()

#Course Fee Vs Rating (Scatter Plot)
plt.figure(figsize=(8,6))
plt.scatter(df['course_fee_inr'], df['rating'], alpha=0.6, color='teal', edgecolor='black')
plt.title("Course Fee vs Rating", fontsize=14)
plt.xlabel("Course Fee (INR)")
plt.ylabel("Rating")
plt.grid(True, linestyle='--', alpha=0.6)
plt.tight_layout()
plt.show()


#Top 10 Most Expensive Courses
top_fees = df.sort_values(by='course_fee_inr',ascending=False).head(10)
plt.figure(figsize = (10,6))
plt.barh(top_fees['course_name'],top_fees['course_fee_inr'],color='plum')
plt.title("Top 10 Most Expensive Courses",fontsize = 14)
plt.xlabel("Course Fee (INR)")
plt.ylabel("Course Name")
plt.gca().invert_yaxis()
plt.tight_layout()
plt.show()


#Colleges Established Over the Years
year_trend = df.groupby('established')['title'].nunique()
plt.figure(figsize = (10,6))
plt.plot(year_trend.index,year_trend.values,marker='o',color='darkblue',linewidth=2)
plt.title("Number of Colleges Established Over the Years",fontsize = 14)
plt.xlabel("Year Established")
plt.ylabel("Number of Colleges")
plt.grid(True,linestyle='--',alpha=0.5)
plt.tight_layout()
plt.show()

#Average Rating by Decade
df['decade'] = (df['established']//10)*10
decade_rating = df.groupby('decade')['rating'].mean()
plt.figure(figsize = (10,6))
plt.bar(decade_rating.index.astype(str),decade_rating.values,color='orange',edgecolor= 'black')
plt.title("Average Rating by Decade of Establishment",fontsize = 14)
plt.xlabel("Decade")
plt.ylabel("Average Rating")
plt.grid(axis='y',linestyle='--',alpha=0.5)
plt.tight_layout()
plt.show()

#Course Duration Distribution (Donut)
if 'course_duration_years' in df.columns:
    duration_dist = df['course_duration_years'].value_counts()
    plt.figure(figsize=(6,6))
    wedges, texts, autotexts = plt.pie(
        duration_dist,
        labels=duration_dist.index,
        autopct='%1.1f%%',
        startangle=140,
        wedgeprops={'edgecolor': 'white'}
    )
    centre_circle = plt.Circle((0,0), 0.70, fc='white')
    fig = plt.gcf()
    fig.gca().add_artist(centre_circle)
    plt.title("Course Duration Distribution", fontsize=14)
    plt.tight_layout()
    plt.show()


