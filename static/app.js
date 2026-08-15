let database;

const form = document.querySelector("#fee-form");
const fields = {
  category: document.querySelector("#category"),
  course: document.querySelector("#course"),
  branch: document.querySelector("#branch"),
  studentType: document.querySelector("#student_type"),
  roomCategory: document.querySelector("#room_category"),
  messOption: document.querySelector("#mess_option"),
  scholarshipEligible: document.querySelector("#scholarship_eligible"),
  scholarshipType: document.querySelector("#scholarship_type"),
  scholarshipPercent: document.querySelector("#scholarship_percent"),
};

function setOptions(select, entries, fallbackLabel = "Select") {
  select.innerHTML = "";
  if (!entries.length) {
    select.append(new Option(fallbackLabel, ""));
    select.disabled = true;
    return;
  }

  entries.forEach(([value, item]) => {
    select.append(new Option(item.label, value));
  });
  select.disabled = false;
}

function selectedBranch() {
  return database.categories[fields.category.value]?.courses?.[fields.course.value]?.branches?.[fields.branch.value];
}

function scholarshipEntries() {
  const branch = selectedBranch();
  const group = branch?.scholarship_group;
  return Object.entries(database.scholarships).filter(([, item]) => {
    return item.groups.includes("all") || item.groups.includes(group);
  });
}

function updateCourses() {
  const courses = database.categories[fields.category.value]?.courses || {};
  setOptions(fields.course, Object.entries(courses), "No courses available");
  updateBranches();
}

function updateBranches() {
  const branches = database.categories[fields.category.value]?.courses?.[fields.course.value]?.branches || {};
  setOptions(fields.branch, Object.entries(branches), "No branches available");
  updateScholarships();
}

function updateHostelFields() {
  const isHosteller = fields.studentType.value === "hosteller";
  fields.roomCategory.disabled = !isHosteller;
  fields.messOption.disabled = !isHosteller;
  fields.roomCategory.required = isHosteller;
  fields.messOption.required = isHosteller;

  if (isHosteller) {
    if (!fields.roomCategory.value) fields.roomCategory.selectedIndex = 0;
    if (!fields.messOption.value) fields.messOption.selectedIndex = 0;
  } else {
    fields.roomCategory.selectedIndex = -1;
    fields.messOption.selectedIndex = -1;
  }
}

function updateScholarships() {
  const eligible = fields.scholarshipEligible.value === "yes";
  const entries = eligible ? scholarshipEntries().filter(([key]) => key !== "none") : [["none", database.scholarships.none]];
  setOptions(fields.scholarshipType, entries.length ? entries : [["none", database.scholarships.none]]);
  fields.scholarshipType.disabled = !eligible;
  updateScholarshipPercentages();
}

function updateScholarshipPercentages() {
  const scholarship = database.scholarships[fields.scholarshipType.value] || database.scholarships.none;
  fields.scholarshipPercent.innerHTML = "";
  scholarship.percentages.forEach((percent) => {
    fields.scholarshipPercent.append(new Option(`${percent}%`, percent));
  });
  fields.scholarshipPercent.disabled = fields.scholarshipEligible.value !== "yes";
}

async function init() {
  database = await fetch("/api/database").then((response) => response.json());
  setOptions(fields.category, Object.entries(database.categories));
  setOptions(fields.roomCategory, Object.entries(database.hostel.rooms));
  setOptions(fields.messOption, Object.entries(database.hostel.mess_options));
  updateCourses();
  updateHostelFields();
}

fields.category.addEventListener("change", updateCourses);
fields.course.addEventListener("change", updateBranches);
fields.branch.addEventListener("change", updateScholarships);
fields.studentType.addEventListener("change", updateHostelFields);
fields.scholarshipEligible.addEventListener("change", updateScholarships);
fields.scholarshipType.addEventListener("change", updateScholarshipPercentages);

form.addEventListener("submit", () => {
  if (fields.scholarshipEligible.value !== "yes") {
    fields.scholarshipType.disabled = false;
    fields.scholarshipPercent.disabled = false;
    fields.scholarshipType.value = "none";
    fields.scholarshipPercent.value = "0";
  }
});

init();
