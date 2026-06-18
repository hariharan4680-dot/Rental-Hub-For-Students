document.addEventListener('DOMContentLoaded', () => {
  const token = localStorage.getItem('token');
  if (!token) return window.location.href = '/login';

  let editingId = null;
  let currentPage = 1;
  let totalPages = 1;
  const limit = 5;

  let isSearching = false;
  let searchParams = {};

  /* ===================== API endpoints ===================== */
  const API = {
    profile: '/api/profile',
    myPosts: '/api/my-posts',
    allPosts: '/api/all-posts',
    search: '/api/search',
    editPost: (id) => `/api/edit-post/${id}`,
    deletePost: (id) => `/api/delete-post/${id}`
  };

  /* ===================== Load Profile ===================== */
  async function loadProfile() {
    try {
      const res = await fetch(API.profile, { headers: { Authorization: `Bearer ${token}` } });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Session expired. Please login again.');
      document.getElementById('userEmail').innerText = data.user.email;
      displayMyPosts(data.rentals || []);
    } catch (err) {
      alert(err.message);
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
  }

  /* ===================== My Posts ===================== */
  async function fetchMyPosts() {
    try {
      const res = await fetch(API.myPosts, { headers: { Authorization: `Bearer ${token}` } });
      const data = await res.json();
      displayMyPosts(data || []);
    } catch (err) {
      console.error(err);
    }
  }

  /* ===================== Create Card ===================== */
  function createCardElement(post, isOwner = true) {
    const div = document.createElement('div');
    div.className = 'rental-card';
    div.dataset.id = post._id;
    div.dataset.title = post.title ?? '';
    div.dataset.description = post.description ?? '';
    div.dataset.location = post.location ?? '';
    div.dataset.price = (post.price ?? post.rent ?? '') + '';
    div.dataset.category = post.category ?? 'room';

    // 🖼️ Add image element
    const img = document.createElement('img');
    img.src = post.image || '/static/placeholder.png';
    img.alt = post.title ?? 'Rental image';
    img.className = 'post-img';

    const title = document.createElement('h3');
    title.innerText = post.title ?? 'Untitled';

    const loc = document.createElement('p');
    loc.innerHTML = `<strong>Location:</strong> ${post.location ?? ''}`;

    const price = document.createElement('p');
    price.innerHTML = `<strong>Price:</strong> ₹${post.price ?? post.rent ?? ''}`;

    const desc = document.createElement('p');
    desc.innerText = post.description ?? '';

    const cat = document.createElement('p');
    cat.innerHTML = `<strong>Category:</strong> ${post.category ?? 'room'}`;

    const btnContainer = document.createElement('div');
    btnContainer.className = 'card-buttons';

    if (isOwner) {
      const editBtn = document.createElement('button');
      editBtn.type = 'button';
      editBtn.className = 'btn-edit';
      editBtn.innerText = '✏️ Edit';
      editBtn.addEventListener('click', () => openEditFormFromCard(div));

      const delBtn = document.createElement('button');
      delBtn.type = 'button';
      delBtn.className = 'btn-delete';
      delBtn.innerText = '🗑️ Delete';
      delBtn.addEventListener('click', () => handleDeletePost(post._id));

      btnContainer.appendChild(editBtn);
      btnContainer.appendChild(delBtn);
    }

    // ✅ Append all elements in order
    div.appendChild(img);     // Add image at the top
    div.appendChild(title);
    div.appendChild(loc);
    div.appendChild(price);
    div.appendChild(desc);
    div.appendChild(cat);
    div.appendChild(btnContainer);

    return div;
  }

  /* ===================== Display My Posts ===================== */
  function displayMyPosts(posts) {
    const postDiv = document.getElementById('rentalsContainer');
    postDiv.innerHTML = '';
    if (!posts || posts.length === 0) {
      postDiv.innerHTML = '<p>No listings found.</p>';
      return;
    }
    posts.forEach(post => {
      const card = createCardElement(post, true);
      postDiv.appendChild(card);
    });
  }

  /* ===================== All Posts ===================== */
  async function fetchAllPosts(page = 1) {
    currentPage = page;
    let url = `${API.allPosts}?page=${currentPage}&limit=${limit}`;

    if (isSearching && Object.keys(searchParams).length > 0) {
      const params = new URLSearchParams({ ...searchParams, page: currentPage, limit });
      url = `${API.search}?${params.toString()}`;
    }

    try {
      const res = await fetch(url);
      const data = await res.json();
      displayAllPosts(data.results || []);
      totalPages = Math.ceil((data.total ?? 0) / limit) || 1;
      const cp = document.getElementById('currentPage');
      if (cp) cp.innerText = currentPage;
      updatePaginationButtons();
    } catch (err) {
      console.error(err);
    }
  }

  function displayAllPosts(posts) {
    const postDiv = document.getElementById('allRentalsContainer');
    postDiv.innerHTML = '';
    if (!posts || posts.length === 0) {
      postDiv.innerHTML = '<p>No listings found.</p>';
      return;
    }
    posts.forEach(post => {
      const card = createCardElement(post, false);
      postDiv.appendChild(card);
    });
  }

  /* ===================== Pagination ===================== */
  window.changePage = function (direction) {
    const newPage = currentPage + direction;
    if (newPage < 1 || newPage > totalPages) return;
    fetchAllPosts(newPage);
  };

  function updatePaginationButtons() {
    const prev = document.getElementById('prevPageBtn');
    const next = document.getElementById('nextPageBtn');
    if (prev) prev.disabled = currentPage === 1;
    if (next) next.disabled = currentPage === totalPages;
  }

  /* ===================== Search ===================== */
  document.getElementById('searchBtn')?.addEventListener('click', () => {
    const title = document.getElementById("searchTitle")?.value;
    const location = document.getElementById("searchLocation")?.value;
    const minPrice = document.getElementById("searchMinPrice")?.value;
    const maxPrice = document.getElementById("searchMaxPrice")?.value;
    const category = document.getElementById("searchCategory")?.value;

    searchParams = {};
    if (title) searchParams.title = title;
    if (location) searchParams.location = location;
    if (minPrice) searchParams.min_price = minPrice;
    if (maxPrice) searchParams.max_price = maxPrice;
    if (category) searchParams.category = category;

    isSearching = true;
    fetchAllPosts(1);
  });

  /* ===================== Edit & Delete Handlers ===================== */
  function openEditFormFromCard(cardEl) {
    editingId = cardEl.dataset.id;
    if (!editingId) return alert('Unable to find post id to edit.');

    const editFormEl = document.getElementById('editForm');
    if (!editFormEl) return alert('Edit form not found in DOM.');

    document.getElementById('editTitle').value = cardEl.dataset.title ?? '';
    document.getElementById('editDescription').value = cardEl.dataset.description ?? '';
    document.getElementById('editPrice').value = cardEl.dataset.price ?? '';
    document.getElementById('editLocation').value = cardEl.dataset.location ?? '';
    document.getElementById('editCategory').value = cardEl.dataset.category ?? '';
    editFormEl.style.display = 'block';
    editFormEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }

  window.closeEditForm = function () {
    editingId = null;
    const editFormEl = document.getElementById('editForm');
    if (editFormEl) editFormEl.style.display = 'none';
  };

  /* ✅ replaced JSON body with FormData for more flexibility */
  window.saveEdit = async function () {
    if (!editingId) return alert('No post selected for editing.');

    const formData = new FormData();
    formData.append('title', document.getElementById('editTitle').value);
    formData.append('description', document.getElementById('editDescription').value);
    formData.append('price', document.getElementById('editPrice').value);
    formData.append('location', document.getElementById('editLocation').value);
    formData.append('category', document.getElementById('editCategory').value);

    try {
      const res = await fetch(API.editPost(editingId), {
        method: 'PUT',
        headers: { Authorization: `Bearer ${token}` }, // no content-type for FormData
        body: formData
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Failed to update');
      alert(data.message || "Post updated successfully!");
      closeEditForm();
      fetchMyPosts();
    } catch (err) {
      alert(err.message);
    }
  };

  async function handleDeletePost(id) {
    if (!id) return alert('No post id provided for delete.');
    if (!confirm("Are you sure you want to delete this post?")) return;
    try {
      const res = await fetch(API.deletePost(id), {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Failed to delete');
      alert(data.message || "Post deleted successfully!");
      fetchMyPosts();
    } catch (err) {
      alert(err.message);
    }
  }

  /* ===================== Logout ===================== */
  window.logout = function () {
    localStorage.removeItem('token');
    alert('Logged out successfully!');
    window.location.href = '/login';
  };

  /* ===================== Initial Load ===================== */
  loadProfile();
  fetchAllPosts();
  fetchMyPosts();
});
