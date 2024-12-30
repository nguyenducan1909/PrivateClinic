//=============== Active cái hover ở trên header =============== 
function navmenuScrollspy() {
    // Logic cho Scrollspy
    console.log('Scrollspy is active');
}

// Gọi hàm navmenuScrollspy
document.addEventListener('DOMContentLoaded', function () {
    navmenuScrollspy(); // Gọi hàm sau khi DOM đã tải xong
});

window.addEventListener('load', navmenuScrollspy);
document.addEventListener('scroll', navmenuScrollspy);

document.addEventListener('DOMContentLoaded', function () {
    const sections = document.querySelectorAll('section');
    const navLinks = document.querySelectorAll('nav ul li a');

    window.addEventListener('scroll', () => {
        let current = '';

        sections.forEach(section => {
            const sectionTop = section.offsetTop;
            const sectionHeight = section.clientHeight;

            // Kiểm tra xem phần nào đang ở trên cùng của viewport
            if (pageYOffset >= sectionTop - sectionHeight / 3) {
                current = section.getAttribute('id');
            }
        });

        // Thay đổi lớp active cho các liên kết trong menu
        navLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href') === '#' + current) {
                link.classList.add('active');
            }
        });
    });
});
//=============== Active cái hover ở trên header =============== 

//=============== Cho các số span tăng dần =============== 
// Hàm khởi chạy đếm số liệu
function startCounting() {
    const counters = document.querySelectorAll('.purecounter');
  
    // Kiểm tra từng phần tử để bắt đầu đếm
    counters.forEach(counter => {
      const start = parseInt(counter.getAttribute('data-purecounter-start'));
      const end = parseInt(counter.getAttribute('data-purecounter-end'));
      const duration = parseInt(counter.getAttribute('data-purecounter-duration'));
      const increment = (end - start) / (duration * 1000); // Tính toán bước nhảy theo thời gian
  
      let currentCount = start;
      counter.textContent = currentCount; // Thiết lập giá trị ban đầu
  
      const updateCounter = () => {
        currentCount += increment; // Tăng giá trị hiện tại
        if (currentCount < end) {
          counter.textContent = Math.floor(currentCount); // Cập nhật nội dung phần tử
          requestAnimationFrame(updateCounter); // Gọi lại hàm này cho lần tiếp theo
        } else {
          counter.textContent = end; // Đảm bảo kết thúc đúng giá trị cuối
        }
      };
  
      requestAnimationFrame(updateCounter); // Bắt đầu đếm
    });
  }
  
  // Kiểm tra vị trí của phần tử trong viewport
  function isElementInViewport(el) {
    const rect = el.getBoundingClientRect();
    return (
      rect.top >= 0 &&
      rect.left >= 0 &&
      rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
      rect.right <= (window.innerWidth || document.documentElement.clientWidth)
    );
  }
  
  // Kiểm tra cuộn trang để chạy đếm
  function checkScroll() {
    const statsSection = document.getElementById('stats');
    if (isElementInViewport(statsSection)) {
      startCounting(); // Bắt đầu đếm nếu phần tử ở trong viewport
      window.removeEventListener('scroll', checkScroll); // Gỡ sự kiện sau khi đã đếm
    }
  }
  
  // Thêm sự kiện cuộn
  window.addEventListener('scroll', checkScroll);
  

//=============== Cho các số span tăng dần =============== 

//=============== Thanh scroll-top  =============== 

// Lấy phần tử scroll-top
const scrollTopBtn = document.getElementById('scroll-top');

// Hàm kiểm tra vị trí cuộn và hiển thị nút
function toggleScrollTopButton() {
  if (window.scrollY > 100) {
    scrollTopBtn.classList.add('active'); // Thêm class active nếu cuộn xuống hơn 100px
  } else {
    scrollTopBtn.classList.remove('active'); // Xóa class active nếu cuộn lên trên 100px
  }
}

// Hàm cuộn lên đầu trang
function scrollToTop() {
  window.scrollTo({
    top: 0,
    behavior: 'smooth' // Cuộn lên một cách mượt mà
  });
}

// Thêm sự kiện cuộn
window.addEventListener('scroll', toggleScrollTopButton);

// Thêm sự kiện click cho nút scroll-top
scrollTopBtn.addEventListener('click', (e) => {
  e.preventDefault(); // Ngăn chặn hành vi mặc định của thẻ <a>
  scrollToTop(); // Gọi hàm cuộn lên đầu trang
});
//=============== Thanh scroll-top  =============== 

//=============== Ẩn hiện câu hỏi  =============== 
// Lấy tất cả các tiêu đề câu hỏi trong phần FAQ
const faqHeaders = document.querySelectorAll('.faq-item h3');

// Thêm sự kiện click cho từng tiêu đề câu hỏi
faqHeaders.forEach(header => {
  header.addEventListener('click', function() {
    // Lấy phần tử cha (faq-item) của tiêu đề đã được nhấn
    const faqItem = this.parentElement;
    // Lấy phần nội dung của câu hỏi
    const content = faqItem.querySelector('.faq-content');

    // Toggle cờ 'faq-active' cho phần mục FAQ
    faqItem.classList.toggle('faq-active');

    // Kiểm tra xem phần mục có đang có cờ 'faq-active' hay không
    if (faqItem.classList.contains('faq-active')) {
      // Hiển thị nội dung nếu có cờ 'faq-active'
      content.style.display = 'block'; // Hiện nội dung
    } else {
      // Ẩn nội dung nếu không có cờ 'faq-active'
      content.style.display = 'none'; // Ẩn nội dung
    }
  });
});
//=============== Ẩn hiện câu hỏi  =============== 